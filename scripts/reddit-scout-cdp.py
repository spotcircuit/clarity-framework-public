#!/usr/bin/env python3
"""
reddit-scout-cdp.py — Find Reddit posts via Chrome CDP and save to Postgres

Uses the debug Chrome (port 9222) to browse subreddits, extract posts,
generate + humanize comments, and save to Postgres.

Run by scout-server.py when popup clicks "Scout Reddit",
or by Paperclip Outreach Agent on schedule.
"""

import sys
import os
import json
import subprocess
import time
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

CDP_URL = "http://localhost:9222"

SUBREDDITS = [
    "ClaudeAI",
    "LocalLLaMA",
    "MachineLearning",
    "SideProject",
    "webdev",
    "devops",
    "artificial",
    "selfhosted",
    "nextjs",
]

SEARCH_KEYWORDS = [
    "Claude Code",
    "agentic AI",
    "MCP server",
]

MAX_PER_SUBREDDIT = 2
MAX_TOTAL = 8

HUMANIZE_PROMPT = """Rewrite this Reddit comment so it sounds like a real person typed it, not AI.

Rules:
- Keep every fact and detail. Do NOT change the meaning.
- Vary sentence length. Short. Then longer. Then short again.
- Use contractions (I've, didn't, it's, that's, won't, here's, we're).
- Can start a sentence with "And" or "But" or "So" or "Honestly" or "FWIW".
- NEVER use em dashes, en dashes, double hyphens, or hyphens as dashes. Only commas, periods, colons, parentheses.
- NEVER use semicolons.
- NEVER use these words: delve, leverage, utilize, harness, cutting-edge, game-changer, revolutionize, tapestry, landscape, pivotal, robust, holistic, streamline, foster, facilitate, empower, navigate, furthermore, moreover, hence.
- Sound like a Redditor, not a LinkedIn poster. Casual tone.
- Can use lowercase sentence starts occasionally.
- Reddit-appropriate contractions and phrasing.
- Keep it under the same word count as the original.

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
    """Classify how well a post matches our services."""
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


def extract_posts_from_subreddit(page, subreddit):
    """Navigate to a subreddit's new posts and extract them."""
    url = f"https://www.reddit.com/r/{subreddit}/new/"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)

    # Scroll down to load more posts
    page.evaluate("window.scrollBy(0, 1500)")
    page.wait_for_timeout(2000)

    posts = page.evaluate("""() => {
        const results = [];
        // Reddit uses shreddit-post web components and also article elements
        const postElements = document.querySelectorAll('shreddit-post, article, [data-testid="post-container"]');

        for (const el of postElements) {
            try {
                let title = '';
                let author = '';
                let score = 0;
                let commentCount = 0;
                let permalink = '';

                // shreddit-post has attributes directly
                if (el.tagName === 'SHREDDIT-POST') {
                    title = el.getAttribute('post-title') || '';
                    author = el.getAttribute('author') || '';
                    score = parseInt(el.getAttribute('score') || '0', 10);
                    commentCount = parseInt(el.getAttribute('comment-count') || '0', 10);
                    permalink = el.getAttribute('permalink') || '';
                } else {
                    // Fallback: parse from DOM
                    const titleEl = el.querySelector('a[data-testid="post-title"], h3, [slot="title"]');
                    title = titleEl ? titleEl.innerText.trim() : '';

                    const authorEl = el.querySelector('a[href*="/user/"], [data-testid="post-author"]');
                    author = authorEl ? authorEl.innerText.replace('u/', '').trim() : '';

                    const scoreEl = el.querySelector('[data-testid="post-score"], faceplate-number, .score');
                    score = scoreEl ? parseInt(scoreEl.innerText.replace(/[^0-9-]/g, '') || '0', 10) : 0;

                    const commentEl = el.querySelector('a[href*="/comments/"] span, [data-testid="comment-count"]');
                    if (commentEl) {
                        commentCount = parseInt(commentEl.innerText.replace(/[^0-9]/g, '') || '0', 10);
                    }

                    const linkEl = el.querySelector('a[href*="/comments/"]');
                    permalink = linkEl ? linkEl.getAttribute('href') : '';
                }

                // Build full URL
                let fullUrl = permalink;
                if (permalink && !permalink.startsWith('http')) {
                    fullUrl = 'https://www.reddit.com' + permalink;
                }

                if (title && title.length > 10) {
                    results.push({
                        title: title.substring(0, 300),
                        author: author || 'Unknown',
                        score: score,
                        commentCount: commentCount,
                        url: fullUrl,
                    });
                }
            } catch (e) {
                // skip malformed elements
            }
        }

        return results.slice(0, 10);
    }""")

    # Now get post body text for each (click into or expand)
    for post in posts:
        post['subreddit'] = subreddit
        post['text'] = post.get('title', '')  # Start with title as text

    # Try to get expanded text from visible post previews
    body_texts = page.evaluate("""() => {
        const results = [];
        const postElements = document.querySelectorAll('shreddit-post, article, [data-testid="post-container"]');
        for (const el of postElements) {
            // Look for post body/preview text
            const bodyEl = el.querySelector('[slot="text-body"], [data-testid="post-body"], .RichTextJSON-root, .md');
            const text = bodyEl ? bodyEl.innerText.trim().substring(0, 500) : '';
            results.push(text);
        }
        return results;
    }""")

    for i, body in enumerate(body_texts):
        if i < len(posts) and body:
            posts[i]['text'] = posts[i]['title'] + '\n\n' + body

    return posts


def search_reddit_keyword(page, keyword):
    """Search Reddit by keyword and extract posts."""
    encoded = keyword.replace(" ", "%20")
    url = f"https://www.reddit.com/search/?q={encoded}&sort=new&t=day"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)

    posts = page.evaluate("""() => {
        const results = [];

        // Search results page uses different DOM than subreddit pages.
        // Try shreddit-post first (subreddit view), then title-link approach (search view).
        const shredditPosts = document.querySelectorAll('shreddit-post');

        if (shredditPosts.length > 0) {
            for (const el of shredditPosts) {
                try {
                    const title = el.getAttribute('post-title') || '';
                    const author = el.getAttribute('author') || '';
                    const score = parseInt(el.getAttribute('score') || '0', 10);
                    const commentCount = parseInt(el.getAttribute('comment-count') || '0', 10);
                    let permalink = el.getAttribute('permalink') || '';
                    let subreddit = (el.getAttribute('subreddit-prefixed-name') || '').replace('r/', '');

                    let fullUrl = permalink;
                    if (permalink && !permalink.startsWith('http')) {
                        fullUrl = 'https://www.reddit.com' + permalink;
                    }

                    if (title && title.length > 10) {
                        results.push({
                            title: title.substring(0, 300),
                            author: author || 'Unknown',
                            score: score,
                            commentCount: commentCount,
                            url: fullUrl,
                            subreddit: subreddit,
                        });
                    }
                } catch (e) {}
            }
        } else {
            // Fallback: search results use a[data-testid="post-title-text"]
            const titleLinks = document.querySelectorAll('a[data-testid="post-title-text"]');
            for (const link of titleLinks) {
                try {
                    const title = link.innerText.trim();
                    const href = link.getAttribute('href') || '';

                    let container = link.parentElement;
                    for (let i = 0; i < 6 && container; i++) container = container.parentElement;

                    let author = '';
                    let subreddit = '';
                    if (container) {
                        const authorEl = container.querySelector('a[href*="/user/"]');
                        author = authorEl ? authorEl.innerText.replace('u/', '').trim() : '';
                        const subEl = container.querySelector('a[href*="/r/"]');
                        if (subEl) {
                            const match = subEl.getAttribute('href').match(/\\/r\\/([^/]+)/);
                            subreddit = match ? match[1] : '';
                        }
                    }

                    let fullUrl = href;
                    if (href && !href.startsWith('http')) {
                        fullUrl = 'https://www.reddit.com' + href;
                    }

                    if (title && title.length > 10) {
                        results.push({
                            title: title.substring(0, 300),
                            author: author || 'Unknown',
                            score: 0,
                            commentCount: 0,
                            url: fullUrl,
                            subreddit: subreddit,
                        });
                    }
                } catch (e) {}
            }
        }

        return results.slice(0, 5);
    }""")

    for post in posts:
        post['text'] = post.get('title', '')
        post['keyword'] = keyword

    return posts


def generate_comment(author, text, subreddit):
    """Generate a Reddit comment via Claude CLI."""
    services_text = ""
    services_file = ROOT / "system" / "outreach" / "services.yaml"
    if services_file.exists():
        services_text = services_file.read_text()[:800]

    # Load subreddit tone info
    strategy_file = ROOT / "system" / "outreach" / "reddit-strategy.yaml"
    tone_hint = ""
    if strategy_file.exists():
        try:
            import yaml
            strategy = yaml.safe_load(strategy_file.read_text())
            tones = strategy.get("subreddit_tones", {})
            if subreddit in tones:
                tone_hint = f"Tone for r/{subreddit}: {tones[subreddit]}"
        except Exception:
            pass

    prompt = f"""You are YOUR_NAME, agentic AI engineer. Write a comment on this Reddit post in r/{subreddit}.

Post by u/{author}: "{text[:600]}"

Your background (for context only, do NOT pitch):
{services_text}

{tone_hint}

Rules:
- Share a specific insight or experience relevant to the post
- If they asked a question, give the actual answer FIRST, then add context
- If it's a "I built this" post, you can mention "I built something similar" if relevant
- DO NOT link to anything. DO NOT mention YOUR_DOMAIN or any URL.
- Sound like a Redditor: casual, can start with "Yeah," or "FWIW" or "Honestly,"
- Technical depth is valued, include code snippets in backticks if relevant
- Under 200 words
- Start with the insight or answer, not "Great post!" or "This resonates"
- NEVER use em dashes, en dashes, double hyphens, or single hyphens as dashes. Only commas, periods, colons, parentheses.
- NEVER use semicolons.

Return ONLY the comment text."""

    result = subprocess.run(
        ["claude", "--print", "-"],
        input=prompt, capture_output=True, text=True, timeout=120,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def humanize(text):
    """Run through humanizer."""
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

            all_posts = []

            # Phase 1: Browse subreddits
            for subreddit in SUBREDDITS:
                print(f"Browsing: r/{subreddit}", flush=True)
                try:
                    posts = extract_posts_from_subreddit(page, subreddit)
                    print(f"  Found {len(posts)} posts", flush=True)

                    # Filter: skip posts we've already scouted
                    fresh = []
                    for post in posts:
                        url = post.get('url', '')
                        if url and db.scouted_post_exists("reddit", url):
                            continue
                        fresh.append(post)

                    # Classify fit and keep only matching posts
                    for post in fresh:
                        fit_level, fit_service = classify_fit(post.get('text', ''))
                        if fit_level != "none":
                            post['fit_level'] = fit_level
                            post['fit_service'] = fit_service
                            all_posts.append(post)

                    total_found += len(posts)
                except Exception as e:
                    print(f"  Error browsing r/{subreddit}: {e}", flush=True)

                # Rate limit between subreddits
                delay = random.uniform(3, 5)
                page.wait_for_timeout(int(delay * 1000))

            # Phase 2: Search by keyword
            for keyword in SEARCH_KEYWORDS:
                print(f"Searching: {keyword}", flush=True)
                try:
                    posts = search_reddit_keyword(page, keyword)
                    print(f"  Found {len(posts)} posts", flush=True)

                    for post in posts:
                        url = post.get('url', '')
                        if url and db.scouted_post_exists("reddit", url):
                            continue
                        fit_level, fit_service = classify_fit(post.get('text', ''))
                        if fit_level != "none":
                            post['fit_level'] = fit_level
                            post['fit_service'] = fit_service
                            all_posts.append(post)

                    total_found += len(posts)
                except Exception as e:
                    print(f"  Error searching '{keyword}': {e}", flush=True)

                delay = random.uniform(3, 5)
                page.wait_for_timeout(int(delay * 1000))

            # Deduplicate by URL
            seen_urls = set()
            unique_posts = []
            for post in all_posts:
                url = post.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_posts.append(post)

            print(f"\n{len(unique_posts)} unique posts with service fit", flush=True)

            # Phase 3: Generate comments (max per subreddit, max total)
            subreddit_counts = {}
            for post in unique_posts:
                if total_drafted >= MAX_TOTAL:
                    print(f"  Reached max total ({MAX_TOTAL}), stopping.", flush=True)
                    break

                sub = post.get('subreddit', 'unknown')
                if subreddit_counts.get(sub, 0) >= MAX_PER_SUBREDDIT:
                    continue

                author = post.get('author', 'Unknown')
                text = post.get('text', '')
                url = post.get('url', '')
                fit_level = post.get('fit_level', 'related')
                fit_service = post.get('fit_service', '')

                print(f"  Drafting for: u/{author[:30]} in r/{sub} [{fit_level}: {fit_service}]...", flush=True)

                raw = generate_comment(author, text, sub)
                if not raw:
                    print(f"  Generation failed, skipping.", flush=True)
                    continue

                humanized = humanize(raw)

                # Save to DB
                scouted_id = db.save_scouted_post(
                    "reddit", author, text,
                    keyword=sub, post_url=url,
                    reactions=post.get('score', 0),
                    comments=post.get('commentCount', 0),
                )
                db.save_drafted_comment(scouted_id, raw, humanized_text=humanized, status="pending")
                total_drafted += 1
                subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
                print(f"  Saved draft (scouted_id={scouted_id})", flush=True)

            page.close()

    except Exception as e:
        print(f"Error: {e}", flush=True)

    db.close()
    print(f"Found {total_found} posts. Drafted {total_drafted} comments.", flush=True)


if __name__ == "__main__":
    main()
