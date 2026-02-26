import requests
import os
from datetime import datetime, timedelta
from collections import Counter
from PIL import Image, ImageDraw, ImageFont

USERNAME = "GlennClaes"
OUTPUT_DIR = "stats_generator/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

    # Commits ophalen (eerste 100 max, GitHub API limit)
    commits = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits").json()
    num_commits = len(commits)
    total_commits += num_commits
    top_repos.append((repo_name, num_commits, repo['stargazers_count']))

# Top 3 languages
top_langs = languages.most_common(3)

# Top 5 contributed repos
top_repos_sorted = sorted(top_repos, key=lambda x: x[1], reverse=True)[:5]

# 3. Commit streak (huidige en langste)
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

# 4. Genereer eenvoudige badge (SVG/PNG) met Pillow als voorbeeld
img = Image.new('RGB', (500, 250), color=(40, 44, 52))
draw = ImageDraw.Draw(img)
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font = ImageFont.truetype(font_path, 20)

draw.text((20,20), f"{USERNAME}'s GitHub Stats", fill=(255,255,255), font=font)
draw.text((20,60), f"Total Commits: {total_commits}", fill=(255,255,255), font=font)
draw.text((20,90), f"Top Languages: {', '.join([lang for lang,_ in top_langs])}", fill=(255,255,255), font=font)
draw.text((20,120), f"Current Streak: {streak} days", fill=(255,255,255), font=font)
draw.text((20,150), "Top Repos:", fill=(255,255,255), font=font)
for idx, (name, commits, stars) in enumerate(top_repos_sorted):
    draw.text((40, 180 + idx*20), f"{name}: {commits} commits, ⭐ {stars}", fill=(255,255,255), font=font)

img.save(f"{OUTPUT_DIR}/github_stats.png")

# 5. Update README.md (simpele include)
with open("README.md", "r") as f:
    readme = f.read()

# vervang oude stats tussen markers
start_marker = "<!-- START GITHUB STATS -->"
end_marker = "<!-- END GITHUB STATS -->"
stats_md = f"{start_marker}\n![GitHub Stats]({OUTPUT_DIR}/github_stats.png)\n{end_marker}"

if start_marker in readme and end_marker in readme:
    pre = readme.split(start_marker)[0]
    post = readme.split(end_marker)[1]
    new_readme = pre + stats_md + post
else:
    new_readme = readme + "\n" + stats_md

with open("README.md", "w") as f:
    f.write(new_readme)