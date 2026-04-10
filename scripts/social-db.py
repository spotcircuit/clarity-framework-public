#!/usr/bin/env python3
"""
social-db.py — Database layer for social media pipeline

Connects to Paperclip's embedded Postgres (localhost:54329).
Used by scout-server, linkedin-monitor, social-daily, and the Chrome extension.

Usage as module:
    from social_db import SocialDB
    db = SocialDB()
    db.save_post("linkedin", "Post text...", topic="services")
    db.save_comment(post_id=1, "linkedin", "Author", "Comment text", "question")
    db.save_reply(comment_id=1, "Draft reply", status="draft")
    db.save_scouted_post("linkedin", "Author", "Post text", keyword="Claude Code")
    db.get_pending_drafts()

Usage as CLI:
    python3 scripts/social-db.py stats
    python3 scripts/social-db.py pending
    python3 scripts/social-db.py posts --limit 5
"""

import sys
import psycopg2
import psycopg2.extras
from datetime import datetime


DB_CONFIG = {
    "host": "localhost",
    "port": 54329,
    "user": "paperclip",
    "password": "paperclip",
    "database": "paperclip",
}


class SocialDB:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.autocommit = True

    def close(self):
        self.conn.close()

    # --- Posts ---

    def save_post(self, platform, text, post_url=None, image_url=None, topic=None, humanized=False):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO social.posts (platform, post_text, post_url, image_url, topic, humanized)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (platform, text, post_url, image_url, topic, humanized))
        return cur.fetchone()[0]

    def get_posts(self, limit=10, platform=None):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if platform:
            cur.execute("SELECT * FROM social.posts WHERE platform=%s ORDER BY created_at DESC LIMIT %s", (platform, limit))
        else:
            cur.execute("SELECT * FROM social.posts ORDER BY created_at DESC LIMIT %s", (limit,))
        return cur.fetchall()

    def update_post_engagement(self, post_id, likes=0, comments=0, reposts=0):
        cur = self.conn.cursor()
        cur.execute("UPDATE social.posts SET likes=%s, comments=%s, reposts=%s WHERE id=%s",
                    (likes, comments, reposts, post_id))
        cur.execute("""
            INSERT INTO social.engagement_log (post_id, likes, comments, reposts)
            VALUES (%s, %s, %s, %s)
        """, (post_id, likes, comments, reposts))

    # --- Comments ---

    def save_comment(self, post_id, platform, author, text, classification=None):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO social.comments (post_id, platform, author_name, comment_text, classification)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (post_id, platform, author, text, classification))
        return cur.fetchone()[0]

    def get_comments(self, post_id):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM social.comments WHERE post_id=%s ORDER BY detected_at", (post_id,))
        return cur.fetchall()

    def comment_exists(self, post_id, author, text_prefix):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM social.comments
            WHERE post_id=%s AND author_name=%s AND comment_text LIKE %s
        """, (post_id, author, text_prefix + '%'))
        return cur.fetchone()[0] > 0

    # --- Replies ---

    def save_reply(self, comment_id=None, post_id=None, draft_text="", humanized_text=None, status="draft"):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO social.replies (comment_id, post_id, draft_text, humanized_text, status)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (comment_id, post_id, draft_text, humanized_text, status))
        return cur.fetchone()[0]

    def update_reply_status(self, reply_id, status, humanized_text=None):
        cur = self.conn.cursor()
        if humanized_text:
            cur.execute("UPDATE social.replies SET status=%s, humanized_text=%s, posted_at=NOW() WHERE id=%s",
                        (status, humanized_text, reply_id))
        else:
            cur.execute("UPDATE social.replies SET status=%s, posted_at=NOW() WHERE id=%s",
                        (status, reply_id))

    def get_pending_replies(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT r.*, c.author_name, c.comment_text, p.post_text
            FROM social.replies r
            LEFT JOIN social.comments c ON r.comment_id = c.id
            LEFT JOIN social.posts p ON r.post_id = p.id
            WHERE r.status = 'draft'
            ORDER BY r.created_at DESC
        """)
        return cur.fetchall()

    # --- Scouted Posts ---

    def save_scouted_post(self, platform, author, text, keyword=None, post_url=None, post_urn=None, reactions=0, comments=0, score=0):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO social.scouted_posts (platform, author_name, post_text, keyword, post_url, post_urn, reactions, comments, relevance_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (platform, author, text, keyword, post_url, post_urn, reactions, comments, score))
        return cur.fetchone()[0]

    def save_drafted_comment(self, scouted_post_id, draft_text, humanized_text=None, status="pending"):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO social.drafted_comments (scouted_post_id, draft_text, humanized_text, status)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (scouted_post_id, draft_text, humanized_text, status))
        return cur.fetchone()[0]

    def get_pending_drafted_comments(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT dc.*, sp.author_name, sp.post_text, sp.platform, sp.post_url
            FROM social.drafted_comments dc
            JOIN social.scouted_posts sp ON dc.scouted_post_id = sp.id
            WHERE dc.status = 'pending'
            ORDER BY dc.created_at DESC
        """)
        return cur.fetchall()

    def update_drafted_comment_status(self, draft_id, status):
        cur = self.conn.cursor()
        cur.execute("UPDATE social.drafted_comments SET status=%s, posted_at=NOW() WHERE id=%s",
                    (status, draft_id))

    # --- Stats ---

    def get_stats(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                (SELECT COUNT(*) FROM social.posts) as total_posts,
                (SELECT COUNT(*) FROM social.posts WHERE platform='linkedin') as linkedin_posts,
                (SELECT COUNT(*) FROM social.posts WHERE platform='facebook') as facebook_posts,
                (SELECT COUNT(*) FROM social.comments) as total_comments,
                (SELECT COUNT(*) FROM social.replies) as total_replies,
                (SELECT COUNT(*) FROM social.replies WHERE status='posted') as posted_replies,
                (SELECT COUNT(*) FROM social.replies WHERE status='draft') as draft_replies,
                (SELECT COUNT(*) FROM social.scouted_posts) as scouted_posts,
                (SELECT COUNT(*) FROM social.drafted_comments WHERE status='pending') as pending_drafts
        """)
        return cur.fetchone()


def main():
    db = SocialDB()

    if len(sys.argv) < 2:
        print("Usage: python3 social-db.py {stats|pending|posts}")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "stats":
        stats = db.get_stats()
        print(f"Posts: {stats['total_posts']} (LinkedIn: {stats['linkedin_posts']}, Facebook: {stats['facebook_posts']})")
        print(f"Comments tracked: {stats['total_comments']}")
        print(f"Replies: {stats['total_replies']} (posted: {stats['posted_replies']}, draft: {stats['draft_replies']})")
        print(f"Scouted posts: {stats['scouted_posts']}")
        print(f"Pending draft comments: {stats['pending_drafts']}")

    elif cmd == "pending":
        drafts = db.get_pending_drafted_comments()
        if not drafts:
            print("No pending drafts.")
        for d in drafts:
            print(f"\n[{d['id']}] {d['platform']} — {d['author_name']}")
            print(f"  Post: {d['post_text'][:80]}...")
            print(f"  Draft: {d['draft_text'][:120]}...")

    elif cmd == "posts":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        posts = db.get_posts(limit=limit)
        for p in posts:
            print(f"[{p['id']}] {p['platform']} {p['posted_at']} — {p['post_text'][:80]}...")

    db.close()


if __name__ == "__main__":
    main()
