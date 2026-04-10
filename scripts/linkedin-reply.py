#!/usr/bin/env python3
"""
linkedin-reply.py — Reply to comments on LinkedIn posts

Usage:
    # Reply to comments on your most recent post
    python3 scripts/linkedin-reply.py --latest --body "Your reply"

    # Reply to comments on a specific post (by content search)
    python3 scripts/linkedin-reply.py --search "Full project context" --body "Your reply"

    # Reply to a specific post by URL
    python3 scripts/linkedin-reply.py --url "https://linkedin.com/feed/update/urn:li:activity:123/" --body "Reply"

    # Reply from file (humanized)
    python3 scripts/linkedin-reply.py --latest --file /tmp/reply.txt

    # Draft mode
    python3 scripts/linkedin-reply.py --latest --body "Reply" --draft
"""

import sys
import os
import argparse
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
ENV_FILE = ROOT_DIR / "system" / ".env"


def load_env():
    if not ENV_FILE.exists():
        print(f"ERROR: {ENV_FILE} not found.")
        sys.exit(1)
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()


def find_post_urn(page, search_text=None, latest=False):
    """Find a post URN by content search or get the latest"""
    page.goto("https://www.linkedin.com/in/brianpyatt/recent-activity/shares/",
              wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    if search_text:
        urn = page.evaluate("""(searchText) => {
            const posts = document.querySelectorAll('[data-urn]');
            for (const post of posts) {
                const text = post.textContent || '';
                if (text.includes(searchText)) {
                    return post.getAttribute('data-urn');
                }
            }
            return null;
        }""", search_text)
    else:
        # Get first (latest) post URN
        urn = page.evaluate("""() => {
            const posts = document.querySelectorAll('[data-urn*="activity"]');
            return posts.length > 0 ? posts[0].getAttribute('data-urn') : null;
        }""")

    return urn


def reply_to_comments(post_url: str, reply_text: str, draft: bool = False):
    """Reply to the first unreplied comment on a LinkedIn post"""
    if draft:
        print("=" * 60)
        print(f"DRAFT REPLY on {post_url}")
        print("=" * 60)
        print(reply_text)
        print("=" * 60)
        return

    load_env()

    from playwright.sync_api import sync_playwright

    li_at = os.environ.get("LINKEDIN_LI_AT", "")
    jsessionid = os.environ.get("LINKEDIN_JSESSIONID", "")
    if not li_at:
        print("ERROR: LINKEDIN_LI_AT not set in system/.env")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        )
        context.add_cookies([
            {"name": "li_at", "value": li_at, "domain": ".www.linkedin.com", "path": "/"},
            {"name": "JSESSIONID", "value": f'"{jsessionid}"' if jsessionid and not jsessionid.startswith('"') else jsessionid, "domain": ".www.linkedin.com", "path": "/"},
        ])

        page = context.new_page()

        # If we need to find the post first
        if not post_url.startswith("http"):
            # It's a search term or "latest"
            search = None if post_url == "latest" else post_url
            print(f"Finding post{' matching: ' + search if search else ' (latest)'}...")
            urn = find_post_urn(page, search_text=search, latest=(post_url == "latest"))
            if not urn:
                print("ERROR: Could not find the post.")
                browser.close()
                sys.exit(1)
            post_url = f"https://www.linkedin.com/feed/update/{urn}/"
            print(f"Found: {post_url}")

        # Navigate to the post
        print(f"Opening post...")
        page.goto(post_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)

        # Find Reply buttons on comments
        reply_btns = page.locator('button:has-text("Reply")').all()
        print(f"Found {len(reply_btns)} comments with Reply buttons")

        if not reply_btns:
            print("No comments to reply to.")
            browser.close()
            return

        # Click first Reply
        reply_btns[0].click()
        print("Clicked Reply on first comment")
        page.wait_for_timeout(2000)

        # Find the reply editor (last visible .ql-editor)
        editors = page.locator('.ql-editor').all()
        editor = None
        for e in reversed(editors):
            try:
                if e.is_visible(timeout=1000):
                    editor = e
                    break
            except:
                continue

        if not editor:
            print("ERROR: Could not find reply editor")
            page.screenshot(path="/tmp/linkedin-reply-debug.png")
            browser.close()
            sys.exit(1)

        # Click at end (after @mention) and type
        editor.click()
        page.keyboard.press("End")
        page.wait_for_timeout(300)

        print("Typing reply...")
        page.keyboard.type(" " + reply_text, delay=2)
        page.wait_for_timeout(1000)

        # Submit
        print("Submitting...")
        submit_btns = page.locator('button.comments-comment-box__submit-button, button.artdeco-button--primary').all()
        submitted = False
        for btn in reversed(submit_btns):
            try:
                if btn.is_visible(timeout=1000):
                    btn.click()
                    submitted = True
                    print("Reply posted!")
                    break
            except:
                continue

        if not submitted:
            page.keyboard.press("Control+Enter")
            print("Reply posted (Ctrl+Enter)")

        page.wait_for_timeout(5000)
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Reply to LinkedIn comments")
    parser.add_argument("--latest", action="store_true", help="Reply to comments on your latest post")
    parser.add_argument("--search", help="Find post by content text")
    parser.add_argument("--url", help="Direct post URL")
    parser.add_argument("--body", "-b", help="Reply text")
    parser.add_argument("--file", "-f", help="Read reply from file")
    parser.add_argument("--draft", action="store_true", help="Preview only")
    args = parser.parse_args()

    # Get reply text
    if args.file:
        reply_text = Path(args.file).read_text().strip()
    elif args.body:
        reply_text = args.body
    else:
        print("ERROR: Provide --body or --file")
        sys.exit(1)

    # Determine post target
    if args.url:
        post_target = args.url
    elif args.search:
        post_target = args.search
    elif args.latest:
        post_target = "latest"
    else:
        print("ERROR: Provide --latest, --search, or --url")
        sys.exit(1)

    reply_to_comments(post_target, reply_text, draft=args.draft)


if __name__ == "__main__":
    main()
