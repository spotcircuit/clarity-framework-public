#!/usr/bin/env python3
"""
linkedin-scout-cdp.py — Find LinkedIn posts via Chrome CDP and save to Postgres

Uses the debug Chrome (port 9222) to search LinkedIn, extract real post URLs,
generate + humanize comments, and save to Postgres.

Run by scout-server.py when popup clicks "Scout Now",
or by Paperclip Outreach Agent on schedule.
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

CDP_URL = "http://localhost:9222"

KEYWORDS = [
    "Claude Code",
    "agentic AI",
    "MCP server",
]

HUMANIZE_PROMPT = """Rewrite this LinkedIn comment so it sounds like a real person typed it, not AI.

Rules:
- Keep every fact and detail. Do NOT change the meaning.
- Vary sentence length. Short. Then longer. Then short again.
- Use contractions (I've, didn't, it's, that's).
- Start one sentence with "And" or "But" or "So" or "Honestly".
- NEVER use em dashes, en dashes, double hyphens, or hyphens as dashes. Only commas, periods, colons, parentheses.
- NEVER use semicolons.
- Sound like a senior engineer talking to a peer.
- Keep it under the same word count.

Original:
{text}

Rewrite (just the text, nothing else):"""


FIT_KEYWORDS = {
    "clarity-framework": {
        "direct": ["clarity framework", "agentic framework", "self-learn loop"],
        "related": ["knowledge base", "context between sessions", "onboarding engineers", "tribal knowledge", "project context", "institutional memory", "fragmented systems", "information architecture", "knowledge layer", "full context", "missing data", "disconnected tools", "toggle tax"],
    },
    "ai-integration": {
        "direct": ["ai integration consulting", "config-driven pipeline"],
        "related": ["api connector", "workflow automation", "n8n", "make.com", "ai in production", "ai pipeline", "production ai"],
    },
    "claude-code": {
        "direct": ["claude code skills", "claude code custom", "mcp server", "model context protocol"],
        "related": ["claude code", "claude agent", "anthropic", "ai coding", "agentic coding", "ai pair programming"],
    },
    "knowledge-base": {
        "direct": ["karpathy wiki pattern"],
        "related": ["knowledge management", "documentation system", "team knowledge", "confluence alternative", "rag system"],
    },
    "doc-pipelines": {
        "direct": ["document processing pipeline"],
        "related": ["pdf processing", "document ai", "ocr", "data extraction", "unstructured data", "ingest pipeline"],
    },
}

def classify_fit(text):
    lower = text.lower()
    for service, kws in FIT_KEYWORDS.items():
        for kw in kws.get("direct", []):
            if kw in lower:
                return "direct", service
    matches = {}
    for service, kws in FIT_KEYWORDS.items():
        count = sum(1 for kw in kws.get("related", []) if kw in lower)
        if count > 0:
            matches[service] = count
    if matches:
        best = max(matches, key=matches.get)
        return "related", best
    return "none", ""


def search_and_extract(page, keyword):
    """Search LinkedIn and extract posts with URLs"""
    encoded = keyword.replace(" ", "%20")
    url = f"https://www.linkedin.com/search/results/content/?keywords={encoded}&datePosted=%22past-24h%22&sortBy=%22date_posted%22"

    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)

    # Extract posts by parsing the visible page text AND clicking into posts for URLs
    posts = page.evaluate("""() => {
        const results = [];
        const main = document.querySelector('main') || document.body;
        const text = main.innerText;

        // Split by Like/Comment patterns to find post boundaries
        const blocks = text.split(/\\n(?=.*?(?:Like|Comment|Repost|Send)\\n)/);

        for (const block of blocks) {
            const lines = block.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
            if (lines.length < 3) continue;

            const skip = ['Like', 'Comment', 'Repost', 'Send', 'Reply', 'Follow',
                'Feed post', 'Boost', 'View analytics', 'Promoted', 'Ad'];

            let author = '';
            let postText = '';

            for (const line of lines) {
                if (skip.includes(line)) continue;
                if (line.match(/^\\d+[mhd]\\s*[·•]/)) continue;
                if (line.match(/^\\d+\\s*(like|comment|repost)/i)) continue;
                if (line.length < 5) continue;

                if (!author && line.length < 50 && line.length > 3) {
                    author = line;
                } else if (!postText && line.length > 80) {
                    postText = line.substring(0, 400);
                    break;
                }
            }

            if (postText && postText.length > 80 && !author.includes('YOUR_NAME')) {
                const lower = postText.toLowerCase();
                const isEvent = lower.includes('meetup.com') || lower.includes('eventbrite') || lower.includes('register now') || lower.includes('join us on') || lower.includes('rsvp');
                const isJob = lower.includes('hiring') || lower.includes('we are looking for') || lower.includes('apply now') || lower.includes('open position') || lower.includes('job opening');
                const isReshare = postText.length < 120 && (lower.includes('http') || lower.includes('.com'));
                const isPromo = lower.includes('use code') || lower.includes('% off') || lower.includes('free trial') || lower.includes('sign up now') || lower.includes('limited time');
                const isCert = lower.includes('certified') || lower.includes('certification') || lower.includes('just passed') || lower.includes('credential');

                if (!isEvent && !isJob && !isReshare && !isPromo && !isCert) {
                    results.push({ author, text: postText });
                }
            }
        }

        return results.slice(0, 5);
    }""")

    # Set keyword on posts
    for post in posts:
        post['url'] = ''
        post['keyword'] = keyword

    # Get URLs: click ... menu → "Copy link to post" → grab "View post" from toast
    menu_authors = page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        const results = [];
        btns.forEach(b => {
            const label = b.getAttribute('aria-label') || '';
            if (label.startsWith('Open control menu for post by')) {
                results.push(label.replace('Open control menu for post by ', ''));
            }
        });
        return results;
    }""")

    for i, menu_author in enumerate(menu_authors[:len(posts)]):
        try:
            # Click the ... menu for this post
            page.evaluate("""(a) => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    if (b.getAttribute('aria-label') === 'Open control menu for post by ' + a) { b.click(); return; }
                }
            }""", menu_author)
            page.wait_for_timeout(1000)

            # Click "Copy link to post"
            page.evaluate("""() => {
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    if (el.innerText?.trim() === 'Copy link to post' && el.offsetHeight > 0) { el.click(); return; }
                }
            }""")
            page.wait_for_timeout(1500)

            # Get URL from "View post" link in toast
            post_url = page.evaluate("""() => {
                const links = document.querySelectorAll('a');
                for (const a of links) {
                    if (a.innerText.trim() === 'View post' && a.href) return a.href;
                }
                return '';
            }""")

            if post_url and i < len(posts):
                posts[i]['url'] = post_url
                # Also fix author name from the menu label
                posts[i]['author'] = menu_author

            # Close toast/menu
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception as e:
            print(f"  URL extraction failed for {menu_author}: {e}", flush=True)

    return posts


def generate_comment(author, text):
    """Generate a comment via Claude CLI"""
    services_text = ""
    services_file = ROOT / "system" / "outreach" / "services.yaml"
    if services_file.exists():
        services_text = services_file.read_text()[:800]

    prompt = f"""You are YOUR_NAME, agentic AI engineer. Write a comment on this LinkedIn post.

Post by {author}: "{text[:400]}"

Your background (for context only, do NOT pitch):
{services_text}

Rules:
- Share a specific insight or experience
- If they asked a question, answer it concretely
- DO NOT link to anything. DO NOT mention your services.
- Sound like a peer sharing knowledge
- Under 100 words
- Start with the insight, not "Great post!"
- NEVER use em dashes, en dashes, or hyphens as dashes. Only commas, periods, colons, parentheses.

Return ONLY the comment text."""

    result = subprocess.run(
        ["claude", "--print", "-"],
        input=prompt, capture_output=True, text=True, timeout=120,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def humanize(text):
    """Run through humanizer"""
    result = subprocess.run(
        ["claude", "--print", "-"],
        input=HUMANIZE_PROMPT.format(text=text),
        capture_output=True, text=True, timeout=120,
    )
    return result.stdout.strip() if result.returncode == 0 else text


def main():
    from social_db import SocialDB

    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        from playwright.sync_api import sync_playwright

    db = SocialDB()
    total_found = 0
    total_drafted = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            page = context.new_page()

            for keyword in KEYWORDS:
                print(f"Searching: {keyword}", flush=True)
                posts = search_and_extract(page, keyword)
                print(f"  Found {len(posts)} posts", flush=True)
                total_found += len(posts)

                for post in posts[:2]:  # max 2 per keyword
                    author = post.get('author', 'Unknown')
                    text = post.get('text', '')
                    url = post.get('url', '')

                    # Check service fit — skip No Fit posts
                    fit_level, fit_service = classify_fit(text)
                    if fit_level == "none":
                        print(f"  Skipping {author[:30]} (no service fit)", flush=True)
                        continue

                    print(f"  Drafting for: {author[:30]} [{fit_level}: {fit_service}]...", flush=True)

                    # Generate comment
                    raw = generate_comment(author, text)
                    if not raw:
                        continue

                    # Humanize
                    humanized = humanize(raw)

                    # Save to DB
                    scouted_id = db.save_scouted_post(
                        "linkedin", author, text,
                        keyword=keyword, post_url=url
                    )
                    db.save_drafted_comment(scouted_id, raw, humanized_text=humanized, status="pending")
                    total_drafted += 1
                    print(f"  Saved draft (scouted_id={scouted_id})", flush=True)

                page.wait_for_timeout(2000)

            page.close()

    except Exception as e:
        print(f"Error: {e}", flush=True)

    db.close()
    print(f"Found {total_found} posts. Drafted {total_drafted} comments.", flush=True)


if __name__ == "__main__":
    main()
