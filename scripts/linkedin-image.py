#!/usr/bin/env python3
"""
linkedin-image.py — Generate LinkedIn post images (diagrams or cards)

Usage:
    python3 scripts/linkedin-image.py --topic services --style card
    python3 scripts/linkedin-image.py --topic clarity --style mermaid
    python3 scripts/linkedin-image.py --topic casestudy --style card
    python3 scripts/linkedin-image.py --custom-html "<html>..." --output /tmp/out.png
"""

import sys
import os
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = ROOT_DIR / "system" / "drafts"

# --- HTML Card Templates ---

CARD_TEMPLATES = {
    "services": """
<!DOCTYPE html>
<html><head><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1200px; height: 627px; background: linear-gradient(135deg, #0a0a0a, #1a1a2e); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: white; display: flex; align-items: center; padding: 60px; }
.left { flex: 1; padding-right: 40px; }
.right { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
h1 { font-size: 42px; font-weight: 800; line-height: 1.1; margin-bottom: 16px; }
h1 span { background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.subtitle { font-size: 18px; color: #94a3b8; line-height: 1.5; }
.card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; }
.card .num { font-size: 14px; color: #60a5fa; font-weight: 700; font-family: monospace; margin-bottom: 6px; }
.card .title { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
.card .desc { font-size: 12px; color: #94a3b8; }
.brand { position: absolute; bottom: 30px; left: 60px; font-size: 14px; color: #475569; font-weight: 600; letter-spacing: 2px; }
</style></head><body>
<div class="left">
  <h1>6 Ways I Help<br>Teams Ship With<br><span>Agentic AI</span></h1>
  <p class="subtitle">Framework licensing, consulting,<br>Claude Code, knowledge bases,<br>data pipelines, open source.</p>
</div>
<div class="right">
  <div class="card"><div class="num">01</div><div class="title">Clarity Framework</div><div class="desc">Open source. Self-learn loop.</div></div>
  <div class="card"><div class="num">02</div><div class="title">AI Integration</div><div class="desc">$150-250/hr consulting.</div></div>
  <div class="card"><div class="num">03</div><div class="title">Claude Code</div><div class="desc">Skills, commands, memory.</div></div>
  <div class="card"><div class="num">04</div><div class="title">Knowledge Bases</div><div class="desc">Karpathy wiki pattern.</div></div>
  <div class="card"><div class="num">05</div><div class="title">Doc Pipelines</div><div class="desc">Multi-format AI ingest.</div></div>
  <div class="card"><div class="num">06</div><div class="title">Build in Public</div><div class="desc">Open source + blog.</div></div>
</div>
<div class="brand">SPOTCIRCUIT.COM</div>
</body></html>""",

    "casestudy": """
<!DOCTYPE html>
<html><head><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1200px; height: 627px; background: linear-gradient(135deg, #0a0a0a, #0f172a); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: white; display: flex; padding: 60px; position: relative; }
.left { flex: 1; display: flex; flex-direction: column; justify-content: center; padding-right: 40px; }
.right { flex: 1; display: flex; flex-direction: column; justify-content: center; }
.tag { display: inline-block; background: rgba(96,165,250,0.15); border: 1px solid rgba(96,165,250,0.3); color: #60a5fa; font-size: 13px; font-weight: 600; padding: 6px 14px; border-radius: 20px; margin-bottom: 20px; font-family: monospace; }
h1 { font-size: 48px; font-weight: 800; line-height: 1.1; margin-bottom: 20px; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.stat { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 24px; text-align: center; }
.stat .number { font-size: 36px; font-weight: 800; background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stat .label { font-size: 13px; color: #94a3b8; margin-top: 6px; }
.brand { position: absolute; bottom: 30px; right: 60px; font-size: 14px; color: #475569; font-weight: 600; letter-spacing: 2px; }
</style></head><body>
<div class="left">
  <div class="tag">CASE STUDY</div>
  <h1>One Session.<br>Entire Site<br>Retooled.</h1>
</div>
<div class="right">
  <div class="stat-grid">
    <div class="stat"><div class="number">53K+</div><div class="label">Lines Deleted</div></div>
    <div class="stat"><div class="number">660</div><div class="label">Lines Added</div></div>
    <div class="stat"><div class="number">38</div><div class="label">301 Redirects</div></div>
    <div class="stat"><div class="number">92.7KB</div><div class="label">Bundle Size</div></div>
  </div>
</div>
<div class="brand">SPOTCIRCUIT.COM</div>
</body></html>""",
}

# --- Mermaid Diagrams ---

MERMAID_TEMPLATES = {
    "clarity": """graph LR
    subgraph Clarity Framework
        A[Raw Files] -->|wiki-ingest| B[Wiki Pages]
        C[SE Commands] -->|discover/brief| D[expertise.yaml]
        D -->|self-improve| E[Validated Knowledge]
        E -->|compounds| D
        B <-->|cross-links| D
    end

    subgraph Three Systems
        F[📄 expertise.yaml<br/>Operational Data]
        G[🧠 .claude/memory<br/>Behavioral Rules]
        H[📚 wiki/<br/>Durable Knowledge]
    end

    style A fill:#1e3a5f,stroke:#60a5fa,color:#fff
    style B fill:#1e3a5f,stroke:#60a5fa,color:#fff
    style C fill:#2d1b4e,stroke:#a78bfa,color:#fff
    style D fill:#2d1b4e,stroke:#a78bfa,color:#fff
    style E fill:#1a3a2a,stroke:#34d399,color:#fff
    style F fill:#1e3a5f,stroke:#60a5fa,color:#fff
    style G fill:#2d1b4e,stroke:#a78bfa,color:#fff
    style H fill:#1a3a2a,stroke:#34d399,color:#fff""",

    "casestudy": """graph TD
    A[Old Site: 36 Directories] -->|retool| B[New Site: 8 Pages]
    A -->|delete| C[53K Lines Removed]
    B -->|add| D[660 Lines Added]
    B --> E[38 Redirects]
    B --> F[Clean Sitemap]
    B --> G[New Schema]

    style A fill:#4a1c1c,stroke:#ef4444,color:#fff
    style B fill:#1a3a2a,stroke:#34d399,color:#fff
    style C fill:#4a1c1c,stroke:#ef4444,color:#fff
    style D fill:#1a3a2a,stroke:#34d399,color:#fff
    style E fill:#1e3a5f,stroke:#60a5fa,color:#fff
    style F fill:#1e3a5f,stroke:#60a5fa,color:#fff
    style G fill:#1e3a5f,stroke:#60a5fa,color:#fff""",
}


def render_html_card(topic: str, output_path: str):
    """Render HTML card to PNG via Playwright"""
    from playwright.sync_api import sync_playwright

    html = CARD_TEMPLATES.get(topic)
    if not html:
        print(f"No card template for topic: {topic}")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 627})
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(500)
        page.screenshot(path=output_path, type="png")
        browser.close()

    print(f"Card saved: {output_path}")


def render_mermaid(topic: str, output_path: str):
    """Render Mermaid diagram to PNG via mermaid-cli"""
    import subprocess
    import tempfile

    mmd = MERMAID_TEMPLATES.get(topic)
    if not mmd:
        print(f"No mermaid template for topic: {topic}")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", delete=False) as f:
        f.write(mmd)
        mmd_path = f.name

    result = subprocess.run(
        ["npx", "-y", "@mermaid-js/mermaid-cli", "-i", mmd_path, "-o", output_path,
         "-b", "transparent", "-w", "1200", "-H", "627",
         "--configFile", "/dev/null"],
        capture_output=True, text=True, timeout=30
    )

    os.unlink(mmd_path)

    if result.returncode != 0:
        print(f"Mermaid render failed: {result.stderr}")
        sys.exit(1)

    print(f"Mermaid saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate LinkedIn post images")
    parser.add_argument("--topic", choices=["services", "clarity", "casestudy"], required=True)
    parser.add_argument("--style", choices=["card", "mermaid"], default="card")
    parser.add_argument("--output", help="Output path (default: system/drafts/linkedin-image-{topic}.png)")
    args = parser.parse_args()

    output = args.output or str(OUTPUT_DIR / f"linkedin-image-{args.topic}.png")

    if args.style == "mermaid":
        render_mermaid(args.topic, output)
    else:
        render_html_card(args.topic, output)


if __name__ == "__main__":
    main()
