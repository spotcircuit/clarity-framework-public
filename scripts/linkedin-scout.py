#!/usr/bin/env python3
"""
linkedin-scout.py — Find relevant LinkedIn posts and draft value-add comments

Usage:
    python3 scripts/linkedin-scout.py                     # Search default keywords
    python3 scripts/linkedin-scout.py --keywords "MCP server,Claude Code"
    python3 scripts/linkedin-scout.py --review             # Review and post saved drafts

Flow:
1. Search LinkedIn for recent posts matching keywords
2. Filter for engagement and relevance
3. Draft value-add comments (no selling, just knowledge)
4. Save to system/drafts/scout/ for review
5. Review mode: read drafts, approve/edit/skip, post approved ones
"""

import sys
import os
import json
import argparse
import time
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
ENV_FILE = ROOT_DIR / "system" / ".env"
SCOUT_DIR = ROOT_DIR / "system" / "drafts" / "scout"
SCOUT_STATE = ROOT_DIR / "system" / "scout-state.json"

DEFAULT_KEYWORDS = [
    "Claude Code",
    "agentic AI engineering",
    "MCP server production",
    "LLM knowledge base",
    "AI context between sessions",
    "Claude Code custom skills",
]


def load_env():
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ[k.strip()] = v.strip()


def load_scout_state():
    if SCOUT_STATE.exists():
        return json.loads(SCOUT_STATE.read_text())
    return {"commented_posts": [], "last_search": None}


def save_scout_state(state):
    SCOUT_STATE.write_text(json.dumps(state, indent=2))


def search_linkedin(keywords):
    """Search LinkedIn for recent posts matching keywords"""
    from playwright.sync_api import sync_playwright

    li_at = os.environ.get("LINKEDIN_LI_AT", "")
    jsessionid = os.environ.get("LINKEDIN_JSESSIONID", "")

    all_posts = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        )
        context.add_cookies([
            {"name": "li_at", "value": li_at, "domain": ".www.linkedin.com", "path": "/"},
            {"name": "JSESSIONID", "value": f'"{jsessionid}"', "domain": ".www.linkedin.com", "path": "/"},
        ])

        page = context.new_page()

        for keyword in keywords[:3]:  # limit to 3 searches per run
            print(f"[scout] Searching: {keyword}")
            encoded = keyword.replace(" ", "%20")
            url = f"https://www.linkedin.com/search/results/content/?keywords={encoded}&datePosted=%22past-24h%22&sortBy=%22date_posted%22"
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)

            # LinkedIn obfuscates classes — parse raw innerText instead
            posts = page.evaluate("""() => {
                const main = document.querySelector('main') || document.body;
                const raw = main.innerText;

                // Split into post blocks by "Follow" or "Like" buttons
                const blocks = raw.split(/(?=Like\\n|\\nComment\\n)/);
                const results = [];

                for (const block of blocks) {
                    const lines = block.split('\\n').map(l => l.trim()).filter(l => l);
                    if (lines.length < 3) continue;

                    // First substantial line is usually author name
                    let author = '';
                    let text = '';
                    let foundAuthor = false;

                    for (const line of lines) {
                        // Skip short lines (timestamps, "Follow", etc)
                        if (line.length < 5) continue;
                        if (['Follow', 'Like', 'Comment', 'Repost', 'Send', 'Feed post', '… more'].includes(line)) continue;
                        if (line.match(/^\\d+[mhd]\\s*•/)) continue;  // timestamp
                        if (line.match(/^•\\s*\\d/)) continue;

                        if (!foundAuthor && line.length < 50 && !line.includes('...')) {
                            author = line;
                            foundAuthor = true;
                        } else if (foundAuthor && line.length > 60) {
                            text = line;
                            break;
                        }
                    }

                    if (author && text && text.length > 60 && !author.includes('YOUR_NAME')) {
                        results.push({
                            urn: '',
                            author: author,
                            text: text.substring(0, 400),
                            reactions: 0,
                            comments: 0,
                        });
                    }
                }

                return results.slice(0, 5);
            }""")

            for post in posts:
                post["keyword"] = keyword
            all_posts.extend(posts)

            page.wait_for_timeout(2000)

        browser.close()

    return all_posts


def score_post(post):
    """Score a post for comment-worthiness"""
    score = 0

    # Engagement signals
    score += min(post.get("reactions", 0), 50)  # cap at 50
    score += min(post.get("comments", 0) * 3, 30)  # comments worth more

    # Text relevance
    text = post.get("text", "").lower()
    high_value = ["struggling with", "anyone using", "how do you", "what's your approach",
                  "looking for", "trying to figure out", "help me understand",
                  "context between sessions", "mcp", "knowledge base", "agentic"]
    for term in high_value:
        if term in text:
            score += 15

    # Questions get bonus (easier to add value)
    if "?" in post.get("text", ""):
        score += 10

    return score


def draft_comment(post):
    """Draft a value-add comment for a post"""
    import subprocess

    prompt = f"""You are YOUR_NAME, a senior agentic AI engineer. You're commenting on someone else's LinkedIn post to add genuine value. NOT to sell anything.

Post by {post['author']}:
"{post['text'][:400]}"

Your background (for context, but don't pitch these):
- Built Clarity Framework: agentic intelligence with self-learn loop, 9 slash commands, Obsidian wiki
- 16 production apps including site-builder, getrankedlocal, SEO tools
- Run 5 autonomous Paperclip agents (daily social posting, wiki curation, etc.)
- Claude Code power user: custom skills, MCP servers, memory systems

Rules:
- Share a specific insight or experience that adds value
- If they asked a question, answer it concretely
- If they shared a challenge, describe how you solved a similar one
- DO NOT link to your website or GitHub
- DO NOT mention your services or offer to help
- DO NOT say "check out my framework"
- Sound like a peer sharing knowledge, not a salesperson
- Under 100 words — comments should be concise
- Start with the insight, not "Great post!" or "This resonates"

Return ONLY the comment text."""

    result = subprocess.run(
        ["claude", "--print", "-"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120,
    )

    return result.stdout.strip() if result.returncode == 0 else None


def save_draft(post, comment):
    """Save a draft comment for review"""
    SCOUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    urn_short = post["urn"].split(":")[-1] if ":" in post.get("urn", "") else "unknown"

    draft = {
        "post_urn": post.get("urn", ""),
        "post_author": post.get("author", ""),
        "post_text": post.get("text", "")[:300],
        "post_reactions": post.get("reactions", 0),
        "post_comments": post.get("comments", 0),
        "keyword": post.get("keyword", ""),
        "draft_comment": comment,
        "created": datetime.now().isoformat(),
        "status": "pending",
    }

    path = SCOUT_DIR / f"{today}-{urn_short}.json"
    path.write_text(json.dumps(draft, indent=2))
    return path


def review_drafts():
    """List pending drafts for review"""
    SCOUT_DIR.mkdir(parents=True, exist_ok=True)
    drafts = sorted(SCOUT_DIR.glob("*.json"))
    pending = []

    for path in drafts:
        draft = json.loads(path.read_text())
        if draft.get("status") == "pending":
            pending.append((path, draft))

    if not pending:
        print("[scout] No pending drafts to review.")
        return

    print(f"[scout] {len(pending)} pending draft(s):\n")
    for i, (path, draft) in enumerate(pending):
        print(f"  [{i+1}] Post by: {draft['post_author']}")
        print(f"      Topic: {draft['post_text'][:80]}...")
        print(f"      Engagement: {draft['post_reactions']} reactions, {draft['post_comments']} comments")
        print(f"      Draft comment: {draft['draft_comment'][:120]}...")
        print(f"      File: {path.name}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Scout LinkedIn for posts to comment on")
    parser.add_argument("--keywords", help="Comma-separated search keywords")
    parser.add_argument("--review", action="store_true", help="Review pending drafts")
    parser.add_argument("--dry-run", action="store_true", help="Search only, no drafts")
    args = parser.parse_args()

    load_env()

    if args.review:
        review_drafts()
        return

    keywords = args.keywords.split(",") if args.keywords else DEFAULT_KEYWORDS
    state = load_scout_state()

    print(f"[scout] Searching LinkedIn for {len(keywords)} keywords...")
    posts = search_linkedin(keywords)
    print(f"[scout] Found {len(posts)} candidate posts")

    # Filter already-commented posts
    commented = set(state.get("commented_posts", []))
    new_posts = [p for p in posts if p.get("urn", "") not in commented]
    print(f"[scout] {len(new_posts)} new (not previously commented)")

    # Score and rank
    scored = [(score_post(p), p) for p in new_posts]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Draft comments for top 3
    drafted = 0
    for score, post in scored[:3]:
        if score < 10:
            continue

        print(f"\n[scout] Post by {post['author']} (score: {score})")
        print(f"  {post['text'][:100]}...")

        if args.dry_run:
            print(f"  DRY RUN — would draft comment")
            continue

        print(f"  Drafting comment...")
        comment = draft_comment(post)

        if comment:
            path = save_draft(post, comment)
            print(f"  Draft saved: {path.name}")
            print(f"  Comment: {comment[:120]}...")
            drafted += 1

    # Update state
    state["last_search"] = datetime.now().isoformat()
    save_scout_state(state)

    print(f"\n[scout] Done. {drafted} draft(s) saved to system/drafts/scout/")
    print(f"[scout] Run with --review to see pending drafts")


if __name__ == "__main__":
    main()
