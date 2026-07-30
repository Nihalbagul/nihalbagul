#!/usr/bin/env python3
"""
Generates three colorful, self-contained SVGs for a GitHub profile README:

  stats.svg   -> total contributions in the last year + a 12-month bar chart
  streak.svg  -> current streak and longest streak
  langs.svg   -> top languages by bytes, across public non-fork repos

Everything is drawn as plain SVG shapes (rects, text, gradients) -- no
external images, no JS, no CSS files -- because GitHub strips <script> and
<link> tags from README content. Colors are inlined as SVG <linearGradient>
and fill attributes so they survive that stripping too.

Run locally for testing:
    GITHUB_TOKEN=ghp_xxx GH_LOGIN=yourusername python3 scripts/generate_stats.py

If GITHUB_TOKEN / GH_LOGIN aren't set, the script falls back to small demo
data so you can preview the visuals without hitting the API.
"""

import os
import sys
import json
import urllib.request
from datetime import datetime, timedelta, timezone

GH_LOGIN = os.environ.get("GH_LOGIN")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# A bright, playful palette used across all three graphics.
PALETTE = ["#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF", "#C77DFF", "#FF922B"]
BG = "#12131A"          # near-black card background
CARD_RADIUS = 18
TEXT_MAIN = "#F5F5F7"
TEXT_DIM = "#9AA0B4"

GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      nodes {
        languages(first: 8, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node { name color }
          }
        }
      }
    }
  }
}
"""


def fetch_github_data():
    """Hits the GitHub GraphQL API. Returns None if creds are missing/fail."""
    if not GH_LOGIN or not GITHUB_TOKEN:
        return None
    body = json.dumps({"query": GRAPHQL_QUERY, "variables": {"login": GH_LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": GH_LOGIN,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        return data["data"]["user"]
    except Exception as e:
        print(f"warning: GitHub API call failed ({e}); using demo data", file=sys.stderr)
        return None


def demo_data():
    """Small synthetic dataset so the script is runnable/testable with no token."""
    today = datetime.now(timezone.utc).date()
    days = []
    for i in range(365, -1, -1):
        d = today - timedelta(days=i)
        # fake but plausible-looking activity pattern
        count = (i * 37) % 9
        if i % 7 in (5, 6):
            count = max(0, count - 4)
        days.append({"date": str(d), "contributionCount": count})
    return {
        "contributionsCollection": {
            "contributionCalendar": {
                "totalContributions": sum(d["contributionCount"] for d in days),
                "weeks": [{"contributionDays": days[i:i + 7]} for i in range(0, len(days), 7)],
            }
        },
        "repositories": {
            "nodes": [
                {"languages": {"edges": [
                    {"size": 42000, "node": {"name": "TypeScript", "color": "#3178c6"}},
                    {"size": 31000, "node": {"name": "Python", "color": "#3572A5"}},
                    {"size": 9000, "node": {"name": "JavaScript", "color": "#f1e05a"}},
                ]}},
                {"languages": {"edges": [
                    {"size": 15000, "node": {"name": "Rust", "color": "#dea584"}},
                    {"size": 5000, "node": {"name": "Python", "color": "#3572A5"}},
                ]}},
            ]
        },
    }


# ---------------------------------------------------------------------------
# Data shaping
# ---------------------------------------------------------------------------

def flatten_days(user):
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        days.extend(w["contributionDays"])
    days.sort(key=lambda d: d["date"])
    return days


def compute_streaks(days):
    current = 0
    longest = 0
    running = 0
    today = str(datetime.now(timezone.utc).date())
    for d in days:
        if d["contributionCount"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    # current streak counts back from the most recent day with contributions
    for d in reversed(days):
        if d["date"] > today:
            continue
        if d["contributionCount"] > 0:
            current += 1
        else:
            if d["date"] == today:
                continue  # today can still be zero and not break the streak
            break
    return current, longest


def monthly_totals(days):
    """Buckets contribution counts into the last 12 calendar months."""
    totals = {}
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        totals[month] = totals.get(month, 0) + d["contributionCount"]
    months = sorted(totals.keys())[-12:]
    return [(m, totals.get(m, 0)) for m in months]


def top_languages(user, top_n=6):
    sizes = {}
    colors = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes[name] = sizes.get(name, 0) + edge["size"]
            colors[name] = edge["node"]["color"] or "#888888"
    ranked = sorted(sizes.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    total = sum(sizes.values()) or 1
    return [(name, size, size / total, colors[name]) for name, size in ranked]


# ---------------------------------------------------------------------------
# SVG drawing helpers
# ---------------------------------------------------------------------------

def card_open(width, height, title):
    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}">
  <defs>
    <linearGradient id="cardbg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1b1c26"/>
      <stop offset="100%" stop-color="#0e0f15"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="{width}" height="{height}" rx="{CARD_RADIUS}" fill="url(#cardbg)"/>
'''


def card_close():
    return "</svg>\n"


def text_el(x, y, s, size=14, fill=TEXT_MAIN, weight="600", family="monospace", anchor="start"):
    s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{s}</text>\n')


def render_stats_svg(days, total):
    width, height = 620, 220
    months = monthly_totals(days)
    max_v = max((v for _, v in months), default=1) or 1
    chart_x, chart_y, chart_w, chart_h = 30, 70, width - 60, 100
    bar_gap = 8
    bar_w = (chart_w - bar_gap * (len(months) - 1)) / max(len(months), 1)

    out = card_open(width, height, "Contribution stats")
    out += text_el(30, 38, "CONTRIBUTIONS", size=13, fill=TEXT_DIM, weight="700")
    out += text_el(30, 60, f"{total:,} in the last year", size=20, weight="800")

    for i, (month, value) in enumerate(months):
        x = chart_x + i * (bar_w + bar_gap)
        h = 4 + (value / max_v) * (chart_h - 4)
        y = chart_y + chart_h - h
        color = PALETTE[i % len(PALETTE)]
        out += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
                f'rx="4" fill="{color}"/>\n')
        label = month[5:7]
        out += text_el(x + bar_w / 2, chart_y + chart_h + 16, label, size=10,
                        fill=TEXT_DIM, weight="500", anchor="middle")

    out += card_close()
    return out


def render_streak_svg(current, longest):
    width, height = 620, 150
    out = card_open(width, height, "Streaks")
    out += text_el(30, 38, "STREAKS", size=13, fill=TEXT_DIM, weight="700")

    boxes = [("current streak", current, PALETTE[0]), ("longest streak", longest, PALETTE[3])]
    box_w = (width - 60 - 20) / 2
    for i, (label, value, color) in enumerate(boxes):
        x = 30 + i * (box_w + 20)
        out += (f'<rect x="{x}" y="55" width="{box_w:.1f}" height="70" rx="14" '
                f'fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="1.5"/>\n')
        out += text_el(x + box_w / 2, 92, f"{value} 🔥" if value else f"{value}",
                        size=24, weight="800", fill=color, anchor="middle", family="monospace")
        out += text_el(x + box_w / 2, 112, label, size=11, fill=TEXT_DIM, anchor="middle")

    out += card_close()
    return out


def render_langs_svg(langs):
    width = 620
    row_h = 26
    height = 60 + row_h * max(len(langs), 1)
    out = card_open(width, height, "Top languages")
    out += text_el(30, 38, "TOP LANGUAGES", size=13, fill=TEXT_DIM, weight="700")

    bar_x, bar_max_w = 170, width - 170 - 90
    y = 62
    for i, (name, _size, frac, color) in enumerate(langs):
        color = color if color.startswith("#") else PALETTE[i % len(PALETTE)]
        out += text_el(30, y + 15, name, size=13, fill=TEXT_MAIN)
        bw = max(6, frac * bar_max_w)
        out += (f'<rect x="{bar_x}" y="{y+2}" width="{bar_max_w}" height="14" rx="7" '
                f'fill="#2a2c3a"/>\n')
        out += (f'<rect x="{bar_x}" y="{y+2}" width="{bw:.1f}" height="14" rx="7" '
                f'fill="{color}"/>\n')
        out += text_el(width - 30, y + 15, f"{frac*100:.1f}%", size=12, fill=TEXT_DIM, anchor="end")
        y += row_h

    out += card_close()
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def write_if_changed(path, content):
    old = None
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            old = f.read()
    if old != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"updated {path}")
    else:
        print(f"unchanged {path}")


def main():
    user = fetch_github_data() or demo_data()
    days = flatten_days(user)
    total = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    current, longest = compute_streaks(days)
    langs = top_languages(user)

    write_if_changed("stats.svg", render_stats_svg(days, total))
    write_if_changed("streak.svg", render_streak_svg(current, longest))
    write_if_changed("langs.svg", render_langs_svg(langs))


if __name__ == "__main__":
    main()
