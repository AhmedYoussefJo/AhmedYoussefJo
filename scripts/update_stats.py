#!/usr/bin/env python3
"""
Dynamic GitHub Stats & Streak Updater
Fetches real-time GitHub data for AhmedYoussefJo and updates:
- assets/github-stats.svg
- assets/github-languages.svg
- assets/github-streak.svg
"""

import os
import re
import sys
import json
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

USERNAME = "AhmedYoussefJo"
TOKEN = os.environ.get("GITHUB_TOKEN")

def get_headers():
    h = {"User-Agent": "StatsUpdater", "Accept": "application/vnd.github.v3+json"}
    if TOKEN:
        h["Authorization"] = f"token {TOKEN}"
    return h

def fetch_json(url, headers=None):
    if headers is None:
        headers = get_headers()
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_streak():
    url = f"https://streak-stats.demolab.com/?user={USERNAME}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            matches = re.findall(r'<text [^>]*>([^<]+)</text>', content)
            cleaned = [m.strip() for m in matches if m.strip()]
            
            # Format usually contains: Total Contributions, Current Streak, Longest Streak
            total_contrib = "142+"
            curr_streak = "2"
            longest_streak = "5"
            
            for i, text in enumerate(cleaned):
                if "Total Contributions" in text and i > 0:
                    total_contrib = cleaned[i-1]
                elif "Current Streak" in text:
                    # look ahead or behind for number
                    if i + 2 < len(cleaned) and cleaned[i+2].isdigit():
                        curr_streak = cleaned[i+2]
                elif "Longest Streak" in text:
                    if i - 1 >= 0 and cleaned[i-1].isdigit():
                        longest_streak = cleaned[i-1]
                    elif i - 2 >= 0 and cleaned[i-2].isdigit():
                        longest_streak = cleaned[i-2]

            return total_contrib, curr_streak, longest_streak
    except Exception as e:
        print(f"[-] Streak fetch fallback: {e}")
        return "142+", "2", "5"

def update_stats_svg(user, total_stars, total_prs, total_commits):
    svg_path = os.path.join("assets", "github-stats.svg")
    if not os.path.exists(svg_path):
        return
    with open(svg_path, "r", encoding="utf-8") as f:
        svg = f.read()

    # Regex replacements for values
    svg = re.sub(
        r'(<text x="24" y="68" class="label">Commits Indexed</text>\s*<text x="180" y="68" [^>]*>)[^<]+(</text>)',
        rf'\g<1>{total_commits}+\g<2>',
        svg
    )
    svg = re.sub(
        r'(<text x="215" y="68" class="label">Pull Requests</text>\s*<text x="386" y="68" [^>]*>)[^<]+(</text>)',
        rf'\g<1>{total_prs}\g<2>',
        svg
    )
    svg = re.sub(
        r'(<text x="24" y="102" class="label">Public Repos</text>\s*<text x="180" y="102" [^>]*>)[^<]+(</text>)',
        rf'\g<1>{user["public_repos"]}\g<2>',
        svg
    )
    svg = re.sub(
        r'(<text x="215" y="102" class="label">Followers</text>\s*<text x="386" y="102" [^>]*>)[^<]+(</text>)',
        rf'\g<1>{user["followers"]}\g<2>',
        svg
    )
    svg = re.sub(
        r'(<text x="24" y="136" class="label">Stars Earned</text>\s*<text x="180" y="136" [^>]*>)[^<]+(</text>)',
        rf'\g<1>{total_stars}\g<2>',
        svg
    )
    svg = re.sub(
        r'(<text x="215" y="136" class="label">Following</text>\s*<text x="386" y="136" [^>]*>)[^<]+(</text>)',
        rf'\g<1>{user["following"]}\g<2>',
        svg
    )

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"    ✓ Updated {svg_path}")

def update_streak_svg(total_contrib, curr_streak, longest_streak, total_pushes, repos_count):
    svg_path = os.path.join("assets", "github-streak.svg")
    if not os.path.exists(svg_path):
        return
    with open(svg_path, "r", encoding="utf-8") as f:
        svg = f.read()

    svg = re.sub(
        r'(id="val-total-contrib">)[^<]+(</text>)',
        rf'\g<1>{total_contrib}\g<2>',
        svg
    )
    svg = re.sub(
        r'(id="val-curr-streak">)[^<]+(</text>)',
        rf'\g<1>{curr_streak} Days 🔥\g<2>',
        svg
    )
    svg = re.sub(
        r'(id="val-longest-streak">)[^<]+(</text>)',
        rf'\g<1>{longest_streak} Days\g<2>',
        svg
    )
    svg = re.sub(
        r'(id="val-total-pushes">)[^<]+(</text>)',
        rf'\g<1>{total_pushes}+\g<2>',
        svg
    )
    svg = re.sub(
        r'(id="val-repos">)[^<]+(</text>)',
        rf'\g<1>{repos_count}\g<2>',
        svg
    )

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"    ✓ Updated {svg_path}")

def update_languages_svg(repos):
    svg_path = os.path.join("assets", "github-languages.svg")
    if not os.path.exists(svg_path):
        return

    lang_totals = {}
    for r in repos:
        if r.get("fork"):
            continue
        try:
            langs = fetch_json(r["languages_url"])
            for l, b in langs.items():
                lang_totals[l] = lang_totals.get(l, 0) + b
        except Exception:
            pass

    total_bytes = sum(lang_totals.values())
    if total_bytes == 0:
        return

    # Sort languages
    sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:5]

    # Colors mapping
    color_map = {
        "Jupyter Notebook": "#DA5B0B",
        "Python": "#3776AB",
        "PowerShell": "#4EAA25",
        "C++": "#00599C",
        "HTML": "#e34c26",
        "CSS": "#563d7c",
        "JavaScript": "#f1e05a",
        "Shell": "#89e051"
    }

    # Total progress bar width = 362, starting x = 24
    bar_width = 362
    curr_x = 24.0

    bar_rects = []
    legend_items = []
    
    legend_y_start = 88
    legend_y_gap = 24

    for idx, (lang, b) in enumerate(sorted_langs):
        pct = (b / total_bytes) * 100
        w = max((b / total_bytes) * bar_width, 3.0)
        c = color_map.get(lang, "#38bdf8")

        if idx == 0:
            bar_rects.append(f'<rect x="{curr_x:.2f}" y="52" width="{w:.2f}" height="7" rx="3.5" fill="{c}"/>')
        elif idx == len(sorted_langs) - 1:
            bar_rects.append(f'<rect x="{curr_x:.2f}" y="52" width="{w:.2f}" height="7" rx="3.5" fill="{c}"/>')
        else:
            bar_rects.append(f'<rect x="{curr_x:.2f}" y="52" width="{w:.2f}" height="7" fill="{c}"/>')

        curr_x += w

        # Legend
        y = legend_y_start + idx * legend_y_gap
        disp_name = "Python (.py)" if lang == "Python" else lang
        legend_items.append(
            f'  <circle cx="28" cy="{y - 4}" r="3.5" fill="{c}"/>\n'
            f'  <text x="42" y="{y}" class="text">{disp_name}</text>\n'
            f'  <text x="386" y="{y}" text-anchor="end" class="label">{pct:.1f}%</text>'
        )

    with open(svg_path, "r", encoding="utf-8") as f:
        svg = f.read()

    # Replace progress bar and legend
    new_bars = f'  <rect x="24" y="52" width="362" height="7" rx="3.5" fill="#1b1e27"/>\n  ' + "\n  ".join(bar_rects)
    new_legend = "\n\n".join(legend_items)

    svg = re.sub(
        r'<!-- Progress Bar Base & Segments -->\s*<rect[^>]+>.*?(?=<!-- Real Language Legend -->)',
        f'<!-- Progress Bar Base & Segments -->\n{new_bars}\n\n  ',
        svg,
        flags=re.DOTALL
    )
    svg = re.sub(
        r'<!-- Real Language Legend -->.*?(?=</svg>)',
        f'<!-- Real Language Legend -->\n{new_legend}\n',
        svg,
        flags=re.DOTALL
    )

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"    ✓ Updated {svg_path}")

def main():
    print("[+] Starting Live GitHub Statistics Updater...")
    # 1. Fetch user
    user = fetch_json(f"https://api.github.com/users/{USERNAME}")
    print(f"    ✓ User: {USERNAME} | Followers: {user['followers']} | Following: {user['following']}")

    # 2. Fetch repos
    repos = fetch_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100")
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    print(f"    ✓ Repos: {len(repos)} | Total Stars: {total_stars}")

    # 3. Fetch PRs
    prs = fetch_json(f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr")
    total_prs = prs.get("total_count", 2)
    print(f"    ✓ Pull Requests: {total_prs}")

    # 4. Fetch Commits
    headers = {**get_headers(), "Accept": "application/vnd.github.cloak-preview"}
    commits = fetch_json(f"https://api.github.com/search/commits?q=author:{USERNAME}", headers=headers)
    total_commits = commits.get("total_count", 249)
    print(f"    ✓ Commits: {total_commits}")

    # 5. Fetch Streak
    total_contrib, curr_streak, longest_streak = fetch_streak()
    print(f"    ✓ Streak: {curr_streak} Days (Current) | {longest_streak} Days (Longest) | Total: {total_contrib}")

    # 6. Update SVGs
    update_stats_svg(user, total_stars, total_prs, total_commits)
    update_languages_svg(repos)
    update_streak_svg(total_contrib, curr_streak, longest_streak, total_commits, user["public_repos"])

    print("[+] Live Stats updated successfully!")

if __name__ == "__main__":
    main()
