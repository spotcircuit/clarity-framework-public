#!/usr/bin/env python3
"""
scout-server.py — Local API server for the LinkedIn Scout Chrome extension

Runs on localhost:9876. The Chrome extension calls this to generate
Claude-powered replies instead of using the built-in templates.

Usage:
    python3 scripts/scout-server.py

The extension falls back to templates if this server isn't running.
"""

import http.server
import json
import subprocess
import sys
from pathlib import Path

# Add scripts dir to path for social_db import
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from social_db import SocialDB
    DB_AVAILABLE = True
    print("[scout-server] Database connected", flush=True)
except Exception as e:
    DB_AVAILABLE = False
    print(f"[scout-server] Database not available: {e}", flush=True)

ROOT = Path(__file__).parent.parent
SERVICES_FILE = ROOT / "system" / "outreach" / "services.yaml"
SETTINGS_FILE = ROOT / "system" / "outreach" / "scout-settings.yaml"

# Load settings
try:
    import yaml
    SETTINGS = yaml.safe_load(SETTINGS_FILE.read_text()) or {}
except Exception:
    SETTINGS = {}

PORT = SETTINGS.get('port', 9876)
REDDIT_USERNAME = SETTINGS.get('reddit_username', '')
LINKEDIN_NAME = SETTINGS.get('linkedin_name', '')
MAX_REPLY_WORDS = SETTINGS.get('max_reply_words', 200)
BANNED_REPEAT_OPENERS = SETTINGS.get('banned_repeat_openers', [])

HUMANIZE_PROMPT_LINKEDIN = """Rewrite this LinkedIn comment so it sounds like a real person typed it, not AI.

Rules:
- Keep every fact and detail. Do NOT change the meaning.
- Vary sentence length aggressively. Short. Then a longer one with a clause or two. Then short again.
- Use contractions (I've, didn't, it's, that's, won't, here's, we're).
- Start one sentence with "And" or "But" or "So" or "Honestly".
- Add one imperfect touch: a parenthetical aside, a trailing thought, a rhetorical question.
- NEVER use em dashes, en dashes, double hyphens, or single hyphens as dashes. Only commas, periods, colons, parentheses.
- NEVER use semicolons.
- NEVER use these words: delve, leverage, utilize, harness, cutting-edge, game-changer, revolutionize, tapestry, landscape, pivotal, robust, holistic, streamline, foster, facilitate, empower, navigate, furthermore, moreover, hence.
- Keep it under the same word count as the original. Don't make it longer.
- Sound like a senior engineer talking to a peer, not a LinkedIn influencer.

Original:
{text}

Rewrite (just the text, nothing else):"""

HUMANIZE_PROMPT_REDDIT = """Rewrite this Reddit comment so it reads like a real person banged it out in 2 minutes.

Rules:
- Keep every fact. Do NOT remove technical details or code snippets.
- CUT THE LENGTH. If over 120 words, cut to under 100. Be ruthless. Real Redditors don't write essays.
- Smash paragraphs together. Max 2 paragraphs. Not 4 or 5.
- Drop transitional phrases. No "practically speaking," no "the deeper fix is," no "what's worked for me:" just say the thing.
- Use contractions everywhere (I've, didn't, it's, that's, won't).
- Start one sentence with "yeah" or "tbh" or "fwiw" (lowercase).
- Leave one small imperfection: a missing comma, a fragment, starting with "like" casually.
- NEVER use em dashes, en dashes, double hyphens. Only commas, periods, colons, parentheses.
- NEVER use semicolons.
- NEVER use: delve, leverage, utilize, harness, cutting-edge, game-changer, revolutionize, tapestry, landscape, pivotal, robust, holistic, streamline, foster, facilitate, empower, navigate, furthermore, moreover, hence.
- Sound like someone typing fast between meetings. Not polished.
- If there's code, keep it but make surrounding text more casual.

Original:
{text}

Rewrite (just the text, nothing else):"""

# Select humanize prompt based on platform
def get_humanize_prompt(post_url=""):
    if "reddit.com" in post_url:
        return HUMANIZE_PROMPT_REDDIT
    return HUMANIZE_PROMPT_LINKEDIN

# Keep backward compat alias
HUMANIZE_PROMPT = HUMANIZE_PROMPT_LINKEDIN


SERVICE_FIT_KEYWORDS = {
    "clarity-framework": {
        "direct": ["clarity framework", "agentic framework", "self-learn loop", "expertise.yaml", "slash commands for claude"],
        "related": ["knowledge base", "context between sessions", "onboarding engineers", "tribal knowledge", "wiki for engineers", "karpathy wiki", "llm wiki", "project context", "institutional memory", "obsidian", "fragmented systems", "information architecture", "knowledge layer", "full context", "context on day one", "missing data", "disconnected tools", "toggle tax"],
    },
    "ai-integration": {
        "direct": ["ai integration consulting", "wire ai into", "config-driven pipeline"],
        "related": ["api connector", "workflow automation", "n8n", "make.com", "zapier", "ai in production", "ai pipeline", "production ai", "ship ai"],
    },
    "claude-code": {
        "direct": ["claude code skills", "claude code custom", "mcp server", "model context protocol", "claude code implementation"],
        "related": ["claude code", "claude agent", "anthropic", "ai coding", "ai pair programming", "agentic coding", "cursor", "copilot alternative"],
    },
    "knowledge-base": {
        "direct": ["karpathy wiki pattern", "knowledge that compounds"],
        "related": ["knowledge management", "documentation system", "team knowledge", "confluence alternative", "notion for engineering", "rag system", "retrieval augmented"],
    },
    "doc-pipelines": {
        "direct": ["document processing pipeline", "multi-format ingest"],
        "related": ["pdf processing", "document ai", "ocr", "data extraction", "unstructured data", "transcript processing", "ingest pipeline"],
    },
    "build-in-public": {
        "direct": [],
        "related": ["build in public", "open source", "indie hacker", "shipping daily", "show your work"],
    },
}

def classify_service_fit(text):
    """Classify how well a post matches our services. Returns (level, service_name)."""
    lower = text.lower()

    # Check direct fit first
    for service, keywords in SERVICE_FIT_KEYWORDS.items():
        for kw in keywords.get("direct", []):
            if kw in lower:
                return "direct", service

    # Check related fit
    matches = {}
    for service, keywords in SERVICE_FIT_KEYWORDS.items():
        count = sum(1 for kw in keywords.get("related", []) if kw in lower)
        if count > 0:
            matches[service] = count

    if matches:
        best = max(matches, key=matches.get)
        if matches[best] >= 2:
            return "related", best
        return "related", best

    return "none", ""


CDP_URL = "http://localhost:9222"

def fetch_full_post_text(post_url):
    """Fetch full post text via Chrome CDP"""
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]

        # Find the about:blank tab (created by the bat file for background work)
        pages = context.pages
        page = None
        for pg in pages:
            if 'about:blank' in pg.url:
                page = pg
                break

        if not page:
            # No blank tab — use the last tab
            page = pages[-1] if pages else context.new_page()

        # Navigate via evaluate to avoid window focus change
        page.evaluate(f"() => window.location.href = '{post_url}'")
        page.wait_for_timeout(5000)

        # Click "...more" to expand
        page.evaluate("""() => {
            const btns = document.querySelectorAll('button, span');
            for (const b of btns) {
                const t = b.innerText.trim();
                if (t === '…more' || t === 'more' || t === '...more' || t === 'See more') {
                    if (b.offsetHeight > 0) { b.click(); break; }
                }
            }
        }""")
        page.wait_for_timeout(1000)

        # Get the main post text — detect platform for different filtering
        is_reddit = 'reddit.com' in post_url
        full_text = page.evaluate("""(isReddit) => {
            // For Reddit: try to get the post title + body + top comments directly
            if (isReddit) {
                let parts = [];
                // Title
                const title = document.title.split(':')[0].trim();
                if (title) parts.push('Title: ' + title);
                // Post body from shreddit-post-text-body or schema:articleBody
                const postBody = document.querySelector('[property="schema:articleBody"], shreddit-post-text-body div, .md.text-14-scalable');
                if (postBody) parts.push('Post: ' + postBody.innerText.trim());
                // Top comments (t1_ prefix = comments, various content selectors)
                const comments = document.querySelectorAll('[id*="-post-rtjson-content"], [id*="-comment-rtjson-content"], .md');
                for (let i = 0; i < Math.min(comments.length, 10); i++) {
                    const text = comments[i].innerText.trim();
                    if (text.length > 20 && text.length < 500) {
                        parts.push('Comment: ' + text);
                    }
                }
                if (parts.length > 0) return parts.join('\\n\\n').substring(0, 3000);
            }
            const main = document.querySelector('main') || document.body;
            const allText = main.innerText;
            const lines = allText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);

            const skipLinkedIn = ['Like', 'Comment', 'Repost', 'Send', 'Reply', 'Follow',
                'Add a comment', 'Most relevant', 'Boost', 'View analytics',
                'Promoted', 'impressions', 'Feed post'];

            const skipReddit = ['Go to', 'Comments Section', 'Top 1% Poster',
                'Join', 'Create a post', 'Community Info', 'Powerups',
                'About Community', 'Rules', 'r/'];

            const skip = isReddit ? skipReddit : skipLinkedIn;

            const meaningful = [];
            for (const line of lines) {
                if (skip.some(s => line === s || line.startsWith(s))) continue;
                if (!isReddit && line.match(/^\\d+[mhdw]\\s*[·•]/)) continue;
                if (!isReddit && line.match(/^\\d+\\s*(like|comment|repost|reaction)/i)) continue;
                if (line.length < 5) continue;
                meaningful.push(line);
            }

            return meaningful.join('\\n').substring(0, 3000);
        }""", is_reddit)

        # Navigate away so the tab doesn't stay on a random post
        page.evaluate("() => window.location.href = 'about:blank'")
        return full_text


class ScoutHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/generate-reply':
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))

            author = body.get('author', 'Someone')
            text = body.get('text', '')
            post_type = body.get('type', 'discussion')
            post_url = body.get('url', '')
            fetch_full = body.get('fetch_full', False)
            is_comment_reply = body.get('is_comment_reply', False)
            thread_context = body.get('thread_context', None)

            # Check DB for ALL our prior comments on this URL (full back-and-forth)
            my_prior_from_db = ""
            my_prior_latest = ""
            if DB_AVAILABLE and post_url:
                try:
                    db_check = SocialDB()
                    cur = db_check.conn.cursor()
                    url_match = f"%{post_url.split('/comments/')[1][:20]}%" if '/comments/' in post_url else f"%{post_url[-30:]}%"
                    cur.execute("""
                        SELECT dc.draft_text, dc.created_at FROM social.drafted_comments dc
                        JOIN social.scouted_posts sp ON dc.scouted_post_id = sp.id
                        WHERE sp.post_url LIKE %s
                        ORDER BY dc.created_at ASC LIMIT 10
                    """, (url_match,))
                    rows = cur.fetchall()
                    if rows:
                        parts = []
                        for i, row in enumerate(rows):
                            parts.append(f"[Comment {i+1}]: {row[0][:300]}")
                        my_prior_from_db = "\n".join(parts)
                        my_prior_latest = rows[-1][0][:150]
                        print(f"[DB] Found {len(rows)} prior comment(s) on this post", flush=True)
                        for i, row in enumerate(rows):
                            print(f"[DB]   [{i+1}] \"{row[0][:60]}...\"", flush=True)
                    cur.close()
                except Exception as e:
                    print(f"[DB] Prior comment check failed: {e}", flush=True)

            # Merge DB priors with thread_context from extension
            if not thread_context:
                thread_context = {}
            if my_prior_from_db and not thread_context.get('my_prior_comment'):
                thread_context['my_prior_comment'] = my_prior_from_db

            if is_comment_reply and text and len(text) > 10:
                # Comment reply: use the comment text passed from DOM directly
                print(f"[COMMENT REPLY] Using comment text from DOM ({len(text)} chars)", flush=True)
                print(f"[THREAD] OP post: {len(thread_context.get('op_post',''))} chars, parents: {len(thread_context.get('parent_chain',[]))}, my prior: {len(thread_context.get('my_prior_comment',''))} chars", flush=True)
            elif post_url and post_url.startswith('http'):
                # Post reply: fetch full post text via CDP
                try:
                    full_text = fetch_full_post_text(post_url)
                    if full_text and len(full_text) > 50:
                        text = full_text
                        print(f"[FULL] Got {len(text)} chars from CDP", flush=True)
                    else:
                        print(f"[FULL] CDP returned empty, using extension text ({len(text)} chars)", flush=True)
                except Exception as e:
                    print(f"[FULL] CDP failed: {e}, using extension text ({len(text)} chars)", flush=True)
            else:
                print(f"[TEXT] No URL, using extension text ({len(text)} chars)", flush=True)

            print(f"\n{'='*60}", flush=True)
            print(f"[REQUEST] author={author}", flush=True)
            print(f"[REQUEST] url={post_url[:80]}", flush=True)
            print(f"[REQUEST] extension text length={len(text)}", flush=True)

            # Classify service fit
            fit_level, fit_service = classify_service_fit(text)
            print(f"[FIT] {fit_level} — {fit_service}", flush=True)
            print(f"[TEXT PREVIEW] {text[:200]}...", flush=True)

            # Detect platform from URL
            is_reddit = "reddit.com" in post_url
            platform = "reddit" if is_reddit else "linkedin"

            # Save to Postgres
            scouted_id = None
            if DB_AVAILABLE:
                try:
                    db = SocialDB()
                    scouted_id = db.save_scouted_post(platform, author, text, keyword=post_type, post_url=post_url)
                    print(f"[DB] Saved scouted_post id={scouted_id}", flush=True)
                except Exception as e:
                    print(f"[DB] Error: {e}", flush=True)

            services_text = SERVICES_FILE.read_text()[:2000] if SERVICES_FILE.exists() else ""

            # Build fit-specific instructions
            if fit_level == "direct":
                fit_instructions = f"Service fit: DIRECT match with {fit_service}. You can mention the tool by name naturally. Don't pitch. One sentence max about it."
            elif fit_level == "related":
                fit_instructions = f"Service fit: RELATED to {fit_service}. Share the technique without naming your product. The insight should stand on its own."
            else:
                fit_instructions = "Service fit: NONE. Pure value-add. Zero mention of tools, products, or services."

            # Detect if the post is a coding challenge or quiz
            text_lower = text.lower()
            is_challenge = any(kw in text_lower for kw in [
                'drop your answers', 'what does this output', 'can you get all correct',
                'coding challenge', 'tricky output', 'what will this print',
                'guess the output', 'interview question', 'solve this',
                'write a function', 'implement', 'how would you'
            ])

            if is_challenge:
                challenge_instructions = (
                    "This post is a coding challenge or quiz. SOLVE IT.\n"
                    "- Give the actual answers with brief explanations\n"
                    "- Then add one deeper insight about what the challenge tests\n"
                    "- Show you actually understand the language mechanics\n"
                    "- Keep it concise but complete\n"
                )
            else:
                challenge_instructions = ""

            if is_reddit:
                # Build thread context for comment replies
                thread_section = ""
                if is_comment_reply and thread_context:
                    tc = thread_context
                    if tc.get('op_post'):
                        thread_section += f"ORIGINAL POST:\n{tc['op_post'][:800]}\n\n"
                    if tc.get('parent_chain'):
                        thread_section += "COMMENT THREAD:\n"
                        for pc in tc['parent_chain']:
                            thread_section += f"  u/{pc['author']} (depth {pc['depth']}): {pc['text'][:300]}\n"
                        thread_section += "\n"
                    if tc.get('my_prior_comment'):
                        thread_section += f"YOUR PREVIOUS COMMENT ON THIS POST (u/{REDDIT_USERNAME}):\n{tc['my_prior_comment'][:400]}\n\n"
                        thread_section += "CRITICAL: You already commented above. Do NOT repeat any points, phrases, or openers from your previous comment. Use a completely different opening word/phrase. Add NEW value only.\n\n"

                if is_comment_reply:
                    context_label = f"Comment by u/{author} (the one you are replying to)"
                else:
                    context_label = f"Post by u/{author}"
                prompt = (
                    f"You are YOUR_NAME, agentic AI engineer. Write a {'reply to this specific comment' if is_comment_reply else 'comment on this Reddit post'}.\n\n"
                    f"{thread_section}"
                    f"{context_label}: {text[:1500]}\n\n"
                    f"{fit_instructions}\n\n"
                    f"{challenge_instructions}"
                    "Rules:\n"
                    "- Share a specific insight or experience relevant to the post\n"
                    "- If they asked a question, give the actual answer FIRST, then add context\n"
                    "- If it's a 'I built this' post, you can mention 'I built something similar' if relevant\n"
                    "- DO NOT link to anything. DO NOT mention YOUR_DOMAIN or any URL.\n"
                    "- Sound like a Redditor: casual, can start with 'Yeah,' or 'FWIW' or 'Honestly,'\n"
                    "- Technical depth is valued, include code snippets in backticks if relevant\n"
                    "- Under 200 words\n"
                    "- Start with the insight or answer, not 'Great post!' or 'This resonates'\n"
                    "- NEVER use em dashes, en dashes, double hyphens, or single hyphens as dashes. Only commas, periods, colons, parentheses.\n\n"
                    "Return ONLY the comment text."
                )
            else:
                # LinkedIn prompt — build prior comment section
                linkedin_prior_section = ""
                if my_prior_from_db:
                    linkedin_prior_section = (
                        f"YOUR PREVIOUS COMMENT ON THIS POST:\n{my_prior_from_db[:400]}\n\n"
                        "CRITICAL: You already commented above. Do NOT repeat any points, phrases, or openers. Use a completely different angle. Add NEW value only.\n\n"
                    )

                if is_comment_reply:
                    linkedin_context = f"You are replying to a comment by {author}: {text[:1500]}"
                else:
                    linkedin_context = f"Post by {author}: {text[:1500]}"

                prompt = (
                    f"You are YOUR_NAME, agentic AI engineer. {'Reply to this comment on a LinkedIn post' if is_comment_reply else 'Reply to this LinkedIn post'}.\n\n"
                    f"{linkedin_prior_section}"
                    f"{linkedin_context}\n\n"
                    f"{fit_instructions}\n\n"
                    f"{challenge_instructions}"
                    "Rules:\n"
                    "- Share a specific insight or experience\n"
                    "- If question: answer it directly with something concrete\n"
                    "- If coding challenge: solve it, then add insight\n"
                    "- Sound like a peer, not a salesperson\n"
                    "- Under 150 words\n"
                    "- Start with the insight or answer, not Great post\n"
                    "- NEVER use em dashes, en dashes, double hyphens, or single hyphens as dashes. Only commas, periods, colons, parentheses.\n\n"
                    "Return ONLY the comment text."
                )


            try:
                result = subprocess.run(
                    ["claude", "--print", "-"],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode == 0:
                    raw_reply = result.stdout.strip()
                    print(f"[RAW] {raw_reply[:80]}...", flush=True)

                    # Humanize the reply (platform-specific prompt)
                    try:
                        humanize_prompt = get_humanize_prompt(post_url)
                        humanize_result = subprocess.run(
                            ["claude", "--print", "-"],
                            input=humanize_prompt.format(text=raw_reply),
                            capture_output=True,
                            text=True,
                            timeout=120,
                        )
                        reply = humanize_result.stdout.strip() if humanize_result.returncode == 0 else raw_reply
                        print(f"[HUMANIZED] {reply[:80]}...", flush=True)
                    except Exception as e:
                        print(f"[HUMANIZE ERROR] {e}", flush=True)
                        reply = raw_reply

                    # Save to Postgres
                    if scouted_id and DB_AVAILABLE:
                        try:
                            db.save_drafted_comment(scouted_id, raw_reply, humanized_text=reply, status="pending")
                            print(f"[DB] Saved draft for scouted_post {scouted_id}", flush=True)
                        except Exception as e:
                            print(f"[DB] Error saving draft: {e}", flush=True)
                    self.send_json(200, {
                        "reply": reply,
                        "fit": fit_level,
                        "service": fit_service,
                        "prior_comment": my_prior_latest if my_prior_latest else "",
                    })
                else:
                    self.send_json(500, {"error": "Claude CLI failed"})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
        elif self.path == '/update-draft':
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            draft_id = body.get('id')
            status = body.get('status', 'skipped')
            if DB_AVAILABLE and draft_id:
                db = SocialDB()
                db.update_drafted_comment_status(draft_id, status)
                self.send_json(200, {"ok": True})
            else:
                self.send_json(400, {"error": "Missing id or DB not available"})

        elif self.path == '/scout':
            content_length = int(self.headers.get('Content-Length', 0))
            print("[SCOUT] Starting LinkedIn scout run...", flush=True)

            try:
                # Run the scout via Playwright CDP (Chrome debug port)
                result = subprocess.run(
                    ["python3", str(ROOT / "scripts" / "linkedin-scout-cdp.py")],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                print(f"[SCOUT] stdout: {result.stdout[:200]}", flush=True)
                if result.returncode == 0:
                    import re
                    found = int(re.search(r'Found (\d+)', result.stdout).group(1)) if re.search(r'Found (\d+)', result.stdout) else 0
                    drafted = int(re.search(r'Drafted (\d+)', result.stdout).group(1)) if re.search(r'Drafted (\d+)', result.stdout) else 0
                    self.send_json(200, {"found": found, "drafted": drafted})
                else:
                    print(f"[SCOUT] stderr: {result.stderr[:200]}", flush=True)
                    self.send_json(500, {"error": "Scout failed", "detail": result.stderr[:200]})
            except Exception as e:
                print(f"[SCOUT] Error: {e}", flush=True)
                self.send_json(500, {"error": str(e)})

        elif self.path == '/scout-reddit':
            content_length = int(self.headers.get('Content-Length', 0))
            print("[SCOUT-REDDIT] Starting Reddit scout run...", flush=True)

            try:
                result = subprocess.run(
                    ["python3", str(ROOT / "scripts" / "reddit-scout-cdp.py")],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                print(f"[SCOUT-REDDIT] stdout: {result.stdout[:200]}", flush=True)
                if result.returncode == 0:
                    import re
                    found = int(re.search(r'Found (\d+)', result.stdout).group(1)) if re.search(r'Found (\d+)', result.stdout) else 0
                    drafted = int(re.search(r'Drafted (\d+)', result.stdout).group(1)) if re.search(r'Drafted (\d+)', result.stdout) else 0
                    self.send_json(200, {"found": found, "drafted": drafted, "platform": "reddit"})
                else:
                    print(f"[SCOUT-REDDIT] stderr: {result.stderr[:200]}", flush=True)
                    self.send_json(500, {"error": "Reddit scout failed", "detail": result.stderr[:200]})
            except Exception as e:
                print(f"[SCOUT-REDDIT] Error: {e}", flush=True)
                self.send_json(500, {"error": str(e)})

        else:
            self.send_json(404, {"error": "Not found"})

    def do_GET(self):
        if self.path == '/health':
            self.send_json(200, {"status": "ok", "service": "scout-server"})

        elif self.path == '/settings':
            self.send_json(200, {
                "reddit_username": REDDIT_USERNAME,
                "linkedin_name": LINKEDIN_NAME,
                "max_reply_words": MAX_REPLY_WORDS,
            })

        elif self.path == '/pending':
            if DB_AVAILABLE:
                try:
                    db = SocialDB()
                    drafts = db.get_pending_drafted_comments()
                    # Serialize datetime objects to strings
                    result = []
                    for d in drafts:
                        row = {}
                        for k, v in dict(d).items():
                            row[k] = v.isoformat() if hasattr(v, 'isoformat') else v
                        result.append(row)
                    self.send_json(200, result)
                except Exception as e:
                    print(f"[ERROR /pending] {e}", flush=True)
                    self.send_json(500, {"error": str(e)})
            else:
                self.send_json(200, [])

        elif self.path == '/stats':
            if DB_AVAILABLE:
                db = SocialDB()
                stats = db.get_stats()
                self.send_json(200, {
                    "pending": stats["pending_drafts"],
                    "posted": stats["posted_replies"],
                    "total_scouted": stats["scouted_posts"],
                    "db": True,
                })
            else:
                self.send_json(200, {"pending": 0, "posted": 0, "db": False})

        else:
            self.send_json(404, {"error": "Not found"})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        import sys
        print(f"[scout-server] {args[0]}", file=sys.stderr, flush=True)


if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', PORT), ScoutHandler)
    print(f"[scout-server] Running on http://localhost:{PORT}")
    print(f"[scout-server] Extension will use Claude CLI for replies")
    print(f"[scout-server] Ctrl+C to stop")
    server.serve_forever()
