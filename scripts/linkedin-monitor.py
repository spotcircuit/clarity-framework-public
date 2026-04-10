#!/usr/bin/env python3
"""
linkedin-monitor.py — Monitor LinkedIn posts for new comments and draft replies

Usage:
    python3 scripts/linkedin-monitor.py                    # Check for new comments
    python3 scripts/linkedin-monitor.py --auto-reply       # Check + auto-reply
    python3 scripts/linkedin-monitor.py --dry-run          # Check only, no posting

Flow:
1. Scrape your recent posts and their comment counts
2. Compare to stored state (system/social-state.json)
3. For new comments: read the comment text
4. Classify the objection type
5. Generate a reply using the outreach framework + humanizer
6. Post the reply (or save as draft)
"""

import sys
import os
import json
import argparse
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
ENV_FILE = ROOT_DIR / "system" / ".env"
STATE_FILE = ROOT_DIR / "system" / "social-state.json"
SERVICES_FILE = ROOT_DIR / "system" / "outreach" / "services.yaml"


def load_env():
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ[k.strip()] = v.strip()


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"posts": {}}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_recent_posts_with_comments():
    """Scrape your recent LinkedIn posts and their comments"""
    from playwright.sync_api import sync_playwright

    li_at = os.environ.get("LINKEDIN_LI_AT", "")
    jsessionid = os.environ.get("LINKEDIN_JSESSIONID", "")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        context.add_cookies([
            {"name": "li_at", "value": li_at, "domain": ".www.linkedin.com", "path": "/"},
            {"name": "JSESSIONID", "value": f'"{jsessionid}"', "domain": ".www.linkedin.com", "path": "/"},
        ])

        page = context.new_page()
        page.goto("https://www.linkedin.com/in/brianpyatt/recent-activity/shares/",
                   wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        # Extract posts with their URNs and comment counts
        posts = page.evaluate("""() => {
            const results = [];
            const postElements = document.querySelectorAll('[data-urn*="activity"]');
            const seen = new Set();

            postElements.forEach(el => {
                const urn = el.getAttribute('data-urn');
                if (!urn || seen.has(urn)) return;
                seen.add(urn);

                const text = el.textContent || '';
                const preview = text.substring(0, 100).trim();

                // Find comment count
                const commentBtn = el.querySelector('button[aria-label*="comment" i]');
                const commentText = commentBtn ? commentBtn.textContent.trim() : '0';
                const commentMatch = commentText.match(/(\d+)/);
                const commentCount = commentMatch ? parseInt(commentMatch[1]) : 0;

                results.push({ urn, preview, commentCount });
            });

            return results.slice(0, 5);
        }""")

        browser.close()
        return posts


def get_new_comments(page, post_urn):
    """Get comment text from a specific post"""
    url = f"https://www.linkedin.com/feed/update/{post_urn}/"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)

    comments = page.evaluate("""() => {
        const comments = [];
        const commentElements = document.querySelectorAll('.comments-comment-item');

        commentElements.forEach(el => {
            const authorEl = el.querySelector('.comments-post-meta__name-text');
            const textEl = el.querySelector('.comments-comment-item__main-content');
            const replyBtn = el.querySelector('button[aria-label*="Reply"]');

            if (authorEl && textEl) {
                const author = authorEl.textContent.trim();
                const text = textEl.textContent.trim();
                // Check if it's not from YOUR_NAME (don't reply to yourself)
                if (!author.includes('YOUR_NAME')) {
                    comments.push({ author, text });
                }
            }
        });

        return comments;
    }""")

    return comments


def classify_comment(comment_text):
    """Classify a comment into action types"""
    text = comment_text.lower().strip()

    # LIKE ONLY — simple compliments, emojis, short praise
    like_patterns = [
        "great post", "love this", "well said", "so true", "spot on",
        "insightful", "thank you", "thanks for sharing", "needed this",
        "bookmarked", "saving this", "following", "subscribed",
        "amazing", "awesome", "brilliant", "nailed it", "100%",
        "this is gold", "fire", "facts",
    ]
    if len(text) < 50 and any(p in text for p in like_patterns):
        return "like"

    # Emoji-only or very short
    if len(text.replace(" ", "")) < 15:
        return "like"

    # LINK REPLY — asking for repo, URL, more info
    link_patterns = [
        "where can i find", "link", "repo", "github", "url",
        "where is this", "how do i get", "where do i sign up",
        "can you share", "send me", "drop the link",
    ]
    if any(p in text for p in link_patterns):
        return "link"

    # QUESTION — asking something specific
    if "?" in text:
        return "question"

    # OBJECTION — skepticism, pushback
    objection_patterns = [
        "expensive", "cost", "price", "budget",
        "tried this before", "doesn't work", "won't work",
        "already have", "we use", "don't need",
        "sounds like", "just another", "how is this different",
    ]
    if any(p in text for p in objection_patterns):
        return "objection"

    # ENGAGEMENT — substantive but not a question or objection
    if len(text) > 100:
        return "engagement"

    # Default: like
    return "like"


LINK_REPLIES = {
    "repo": "Here's the repo: https://github.com/spotcircuit/clarity-framework",
    "github": "GitHub: https://github.com/spotcircuit/clarity-framework",
    "default": "More details here: https://www.YOUR_DOMAIN/clarity",
}


def draft_reply(comment_text, commenter_name, comment_type):
    """Generate appropriate reply based on comment type"""
    import subprocess

    if comment_type == "like":
        return None  # Just like, no reply

    if comment_type == "link":
        # Figure out what they want
        text = comment_text.lower()
        if "repo" in text or "github" in text or "code" in text:
            return LINK_REPLIES["repo"]
        return LINK_REPLIES["default"]

    # For questions, objections, engagement — use Claude
    services_text = SERVICES_FILE.read_text()[:2000] if SERVICES_FILE.exists() else ""

    prompt = f"""You are YOUR_NAME, agentic AI engineer. Reply to this LinkedIn comment.

Comment from {commenter_name}: "{comment_text}"
Comment type: {comment_type}

Your services context:
{services_text}

Rules:
- {"Answer the technical question directly. Be specific." if comment_type == "question" else ""}
- {"Lead with evidence, not enthusiasm. Reference a specific proof point." if comment_type == "objection" else ""}
- {"Add one useful insight they can apply. Don't just agree." if comment_type == "engagement" else ""}
- Under 150 words for a comment reply
- Sound like an engineer talking to a peer
- No "Great question!" openers
- Include a link to YOUR_DOMAIN or the GitHub repo if relevant

Return ONLY the reply text."""

    result = subprocess.run(
        ["claude", "--print", "-"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120,
    )

    return result.stdout.strip() if result.returncode == 0 else None


def humanize_reply(reply_text):
    """Run through humanizer"""
    import subprocess
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts" / "humanize.py"), reply_text],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout.strip() if result.returncode == 0 else reply_text


def post_reply(post_urn, reply_text):
    """Post a reply using linkedin-reply.py"""
    import subprocess
    url = f"https://www.linkedin.com/feed/update/{post_urn}/"
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts" / "linkedin-reply.py"),
         "--url", url, "--body", reply_text],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Monitor LinkedIn for new comments")
    parser.add_argument("--auto-reply", action="store_true", help="Auto-reply to new comments")
    parser.add_argument("--dry-run", action="store_true", help="Check only, no posting")
    args = parser.parse_args()

    load_env()
    state = load_state()

    print("[monitor] Checking recent posts for new comments...")
    posts = get_recent_posts_with_comments()

    new_comments_found = 0

    for post in posts:
        urn = post["urn"]
        current_count = post["commentCount"]
        known_count = state["posts"].get(urn, {}).get("commentCount", 0)

        if current_count > known_count:
            diff = current_count - known_count
            print(f"\n[monitor] NEW: {diff} new comment(s) on post: {post['preview'][:60]}...")
            new_comments_found += diff

            if args.auto_reply or args.dry_run:
                replied_comments = state["posts"].get(urn, {}).get("repliedTo", [])
                comment_text = f"(New comment on post about: {post['preview'][:80]})"

                # Classify the comment
                comment_type = classify_comment(comment_text)
                print(f"[monitor] Type: {comment_type}")

                if comment_type == "like":
                    print(f"[monitor] → Like only (no reply needed)")
                else:
                    reply = draft_reply(comment_text, "commenter", comment_type)

                    if reply:
                        print(f"[monitor] Draft reply ({comment_type}):\n  {reply[:200]}...")

                        if not args.dry_run and args.auto_reply:
                            # Humanize unless it's a short link reply
                            if comment_type != "link":
                                reply = humanize_reply(reply)
                            success = post_reply(urn, reply)
                            if success:
                                print(f"[monitor] Reply posted!")
                            else:
                                print(f"[monitor] Reply failed — saved as draft")
                                draft_path = ROOT_DIR / "system" / "drafts" / f"reply-{urn.split(':')[-1]}.md"
                                draft_path.write_text(reply)
                        elif args.dry_run:
                            print("[monitor] DRY RUN — not posting")

        # Update state
        state["posts"][urn] = {
            "commentCount": current_count,
            "preview": post["preview"][:100],
            "lastChecked": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    save_state(state)

    if new_comments_found == 0:
        print("[monitor] No new comments found.")
    else:
        print(f"\n[monitor] Total: {new_comments_found} new comment(s)")


if __name__ == "__main__":
    main()
