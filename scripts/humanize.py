#!/usr/bin/env python3
"""
humanize.py — Rewrite AI-generated text to sound like a real person

Usage:
    python3 scripts/humanize.py "Your AI-sounding text here"
    python3 scripts/humanize.py --file system/drafts/linkedin-2026-04-08.md
    echo "text" | python3 scripts/humanize.py --stdin

Uses Claude API (ANTHROPIC_API_KEY from environment).
"""

import sys
import os
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
ENV_FILE = ROOT_DIR / "system" / ".env"

HUMANIZE_PROMPT = """You are YOUR_NAME, a senior engineer who builds agentic AI systems. You're rewriting a LinkedIn post so it sounds like YOU wrote it, not an AI.

## YOUR VOICE
- Direct. Confident. Technical but accessible.
- You explain things like you're talking to a smart colleague over coffee.
- You occasionally start sentences with "And" or "But" or "So".
- You use contractions naturally (I'm, didn't, won't, it's, that's, here's).
- You sometimes use a parenthetical aside (like this one) or a trailing thought.
- Your sentences range from 3 words to 35. Some paragraphs are one sentence. Others are three.

## BURSTINESS RULES (critical for sounding human)
- Alternate sentence lengths aggressively. Short. Then a longer one that unpacks the idea with specifics and maybe a clause or two. Then short again.
- Never write 3+ sentences in a row that are similar length.
- Start at least one paragraph with a single word or very short phrase.
- End at least one thought with a question.
- Break one "rule" of grammar on purpose (fragment, starting with And, ending with a preposition).

## WHAT TO KEEP
- Every fact, number, URL, and link — exactly as-is. Do NOT invent or change data.
- The core argument and structure of the post.
- Hashtags at the end (max 5). Always include #AgenticAI.
- Keep it under 3000 chars.

## WHAT TO CHANGE
- Rewrite any sentence that sounds like a press release or product marketing.
- Convert numbered lists into flowing prose unless the list genuinely helps readability.
- Replace the opening if it's generic. First line should make someone stop scrolling. Lead with the most surprising or concrete detail.
- Cut filler. If a sentence doesn't add information or personality, kill it.

## BANNED WORDS (these scream AI)
Never use: delve, embark, tapestry, leverage, utilize, utilizing, harness, cutting-edge, game-changer, revolutionize, disruptive, groundbreaking, remarkable, elevate, unlock, unleash, realm, landscape, shed light, illuminate, unveil, pivotal, intricate, elucidate, furthermore, moreover, hence, however, in conclusion, in summary, testament, ever-evolving, navigate, navigating, seamlessly, robust, holistic, synergy, paradigm, innovative, foster, facilitate, empower, streamline, optimize

## BANNED PATTERNS
- Never start with "I'm excited to" or "Thrilled to share" or "Just shipped"
- Never use "not just X, but also Y" constructions
- NEVER use em dashes (—) anywhere. Not once. Replace with commas, periods, colons, or parentheses.
- NEVER use en dashes (–) anywhere. Same rule.
- NEVER use double hyphens (--) anywhere. Same rule.
- NEVER use a single hyphen as a dash ( - ) between clauses. Hyphens are ONLY for compound words like "self-learn" or "open-source".
- Only allowed punctuation for connecting ideas: commas, periods, colons, parentheses.
- Never use semicolons.
- Avoid "In today's world" or "In the age of AI" openings.

## FORMAT
Return ONLY the rewritten post. No preamble, no "Here's the rewrite:", no explanation.

---
ORIGINAL POST:
{text}
---"""


def load_env():
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ[key.strip()] = value.strip()


def humanize(text: str) -> str:
    """Rewrite text using claude CLI (uses your subscription, no API key needed)"""
    import subprocess

    prompt = HUMANIZE_PROMPT.format(text=text)

    result = subprocess.run(
        ["claude", "--print", "-"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        print(f"ERROR: claude CLI failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Humanize AI-generated text")
    parser.add_argument("text", nargs="?", help="Text to humanize")
    parser.add_argument("--file", help="Read from file")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    parser.add_argument("--in-place", action="store_true", help="Overwrite the input file with humanized version")
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    elif args.file:
        text = Path(args.file).read_text()
    elif args.text:
        text = args.text
    else:
        parser.print_help()
        sys.exit(1)

    # Strip draft header/footer if present
    lines = text.strip().split("\n")
    clean_lines = [l for l in lines if not l.startswith("===") and "DRAFT" not in l and "Characters:" not in l]
    text = "\n".join(clean_lines).strip()

    result = humanize(text)
    print(result)

    if args.in_place and args.file:
        Path(args.file).write_text(result)
        print(f"\nOverwritten: {args.file}", file=sys.stderr)


if __name__ == "__main__":
    main()
