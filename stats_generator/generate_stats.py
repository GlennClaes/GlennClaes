import requests
import os
from datetime import datetime
from collections import Counter
import svgwrite

USERNAME = "GlennClaes"
OUTPUT_DIR = "stats_generator/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_SVG = f"{OUTPUT_DIR}/github_stats.svg"

# 1. Haal alle public repos op
repos = requests.get(f"https://api.github.com/users/{USERNAME}/repos").json()

# 2. Verzamel stats
total_commits = 0
languages = Counter()
top_repos = []

for repo in repos:
    repo_name = repo['name']
    lang = repo['language'] or "Other"
    languages[lang] += 1

    commits = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits").json()
    num_commits = len(commits)
    total_commits += num_commits
    top_repos.append((repo_name, num_commits, repo['stargazers_count']))

# Top 3 languages
top_langs = languages.most_common(3)
# Top 5 repos
top_repos_sorted = sorted(top_repos, key=lambda x: x[1], reverse=True)[:5]

# 3. Commit streak
all_commit_dates = []
for repo in repos:
    commits = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo['name']}/commits").json()
    all_commit_dates.extend([c['commit']['author']['date'][:10] for c in commits])

all_commit_dates = sorted(list(set(all_commit_dates)))
today = datetime.utcnow().date()
streak = 0
for i in range(len(all_commit_dates)-1, -1, -1):
    date_obj = datetime.strptime(all_commit_dates[i], "%Y-%m-%d").date()
    if (today - date_obj).days == streak:
        streak += 1
    else:
        break

# 4. Genereer SVG
dwg = svgwrite.Drawing(OUTPUT_SVG, size=("650px", "350px"))
dwg.add(dwg.rect(insert=(0,0), size=("100%","100%"), fill="#1e1e2f"))

# Header
dwg.add(dwg.text(f"{USERNAME}'s GitHub Stats", insert=(20,40), fill="white", font_size="26px", font_weight="bold"))
dwg.add(dwg.text(f"Total Commits: {total_commits}", insert=(20,75), fill="white", font_size="18px"))
dwg.add(dwg.text(f"Current Streak: {streak} days", insert=(20,100), fill="white", font_size="18px"))

# Top languages met gekleurde cirkels
x, y = 20, 140
colors = ["#f1e05a", "#3572A5", "#563d7c"]  # voorbeeld kleuren
for i, (lang, count) in enumerate(top_langs):
    dwg.add(dwg.circle(center=(x, y), r=10, fill=colors[i % len(colors)]))
    dwg.add(dwg.text(f"{lang} ({count})", insert=(x+20, y+5), fill="white", font_size="16px"))
    y += 30

# Top repositories
y = 230
dwg.add(dwg.text("Top Repos:", insert=(20, y), fill="white", font_size="18px"))
y += 25
for name, commits, stars in top_repos_sorted:
    dwg.add(dwg.text(f"{name}: {commits} commits, ⭐ {stars}", insert=(40, y), fill="white", font_size="16px"))
    y += 20

dwg.save()
print(f"SVG saved to {OUTPUT_SVG}")

# 5. Update README.md
with open("README.md", "r") as f:
    readme = f.read()

start_marker = "<!-- START GITHUB STATS -->"
end_marker = "<!-- END GITHUB STATS -->"
stats_md = f"{start_marker}\n![GitHub Stats]({OUTPUT_SVG})\n{end_marker}"

if start_marker in readme and end_marker in readme:
    pre = readme.split(start_marker)[0]
    post = readme.split(end_marker)[1]
    new_readme = pre + stats_md + post
else:
    new_readme = readme + "\n" + stats_md

with open("README.md", "w") as f:
    f.write(new_readme)