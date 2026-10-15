#!/usr/bin/env python3
"""Render public GitHub data as repository-hosted SVGs, without external widgets."""
import argparse
import collections
import datetime as dt
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import urllib.request

USER = 'Achyuth777'
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
TODAY = dt.datetime.now(dt.timezone.utc).date()


def fetch(url):
    headers = {'User-Agent': 'Achyuth777-profile', 'Accept': 'application/vnd.github+json'}
    if url.startswith('https://api.github.com/') and os.getenv('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return r.read().decode()


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells, self.tips = {}, {}
        self.target, self.text = None, ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and a.get('data-date'):
            self.cells[a['id']] = {'date': a['data-date'], 'level': int(a['data-level'])}
        if tag == 'tool-tip':
            self.target, self.text = a.get('for'), ''

    def handle_data(self, text):
        if self.target:
            self.text += text

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.target:
            self.tips[self.target] = self.text.strip()
            self.target = None

    def days(self):
        out = []
        for key, cell in self.cells.items():
            tip = self.tips.get(key, '')
            match = re.match(r'([\d,]+) contribution', tip)
            if not match and not tip.startswith('No contributions'):
                raise ValueError('GitHub calendar format changed; keeping previous assets')
            out.append({**cell, 'count': int(match[1].replace(',', '')) if match else 0})
        if len(out) < 350:
            raise ValueError('Incomplete contribution calendar; keeping previous assets')
        return sorted(out, key=lambda x: x['date'])


def text(x, y, value, size=16, fill='#94a3b8', weight=400):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}">{html.escape(str(value))}</text>'


def svg(title, height, content):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="840" height="{height}" viewBox="0 0 840 {height}" role="img" aria-label="{html.escape(title)}">
<title>{html.escape(title)}</title><style>text{{font-family:Inter,Segoe UI,Arial,sans-serif}}.snake{{animation:travel 22s linear infinite}}@keyframes travel{{to{{stroke-dashoffset:-1000}}}}@media(prefers-reduced-motion:reduce){{.snake{{animation:none;opacity:0}}}}</style>
<rect x="1" y="1" width="838" height="{height-2}" rx="18" fill="#0d1424" stroke="#283449"/>{content}</svg>'''


def render(user, repos, languages, days):
    counts = {d['date']: d['count'] for d in days}
    longest = running = 0
    for d in days:
        running = running + 1 if d['count'] else 0
        longest = max(longest, running)
    end = TODAY if counts.get(TODAY.isoformat(), 0) else TODAY - dt.timedelta(days=1)
    current = 0
    while counts.get(end.isoformat(), 0):
        current += 1
        end -= dt.timedelta(days=1)
    stars = sum(r['stargazers_count'] for r in repos if not r['fork'])
    metrics = [('PUBLIC REPOS', user['public_repos']), ('STARS · OWN REPOS', stars), ('FOLLOWERS', user['followers']),
               ('CONTRIBUTIONS', sum(d['count'] for d in days)), ('CURRENT STREAK', f'{current} days'), ('BEST IN VIEW', f'{longest} days')]
    body = text(28, 35, 'GITHUB / THE NUMBERS', 15, '#67e8f9', 600)
    for i, (label, value) in enumerate(metrics):
        x, y = 28 + i % 3 * 272, 88 + i // 3 * 88
        body += text(x, y, value, 34, '#f1f5f9', 700) + text(x, y+23, label, 12, '#9caec5')
    body += text(28, 246, f'Public data · calendar streaks use UTC · updated {TODAY.isoformat()}', 12)
    result = {'stats.svg': svg('Public GitHub statistics for Achyuth PV', 266, body)}

    totals = collections.Counter()
    for langs in languages.values():
        totals.update(langs)
    if not totals:
        raise ValueError('No language data returned')
    top = totals.most_common(5)
    if len(totals) > 5:
        top.append(('Other', sum(totals.values()) - sum(n for _, n in top)))
    colors = ['#67e8f9', '#a78bfa', '#34d399', '#fbbf24', '#fb7185', '#64748b']
    body = text(28, 35, 'LANGUAGES / PUBLIC CODE', 15, '#a78bfa', 600)
    x, total = 28, sum(totals.values())
    for i, (lang, count) in enumerate(top):
        w = count / total * 784
        body += f'<rect x="{x:.2f}" y="61" width="{w:.2f}" height="16" fill="{colors[i]}"/>'
        x += w
        lx, ly = 28 + (i % 3) * 272, 110 + (i // 3) * 38
        body += f'<circle cx="{lx+5}" cy="{ly-5}" r="5" fill="{colors[i]}"/>'
        body += text(lx+18, ly, f'{lang} {count/total*100:.1f}%', 15, '#e2e8f0')
    body += text(28, 190, 'Share of language bytes in non-fork public repositories; not a skill rating.', 12)
    result['languages.svg'] = svg('Languages by bytes across public non-fork repositories', 212, body)

    first = dt.date.fromisoformat(days[0]['date'])
    origin = first - dt.timedelta(days=(first.weekday()+1) % 7)
    weeks = ((dt.date.fromisoformat(days[-1]['date'])-origin).days // 7) + 1
    step = min(14, 784 / weeks)
    body = text(28, 35, 'ACTIVITY / A YEAR OF BUILDING', 15, '#67e8f9', 600)
    palette = ['#1b263a', '#164e63', '#0e7490', '#22d3ee', '#a5f3fc']
    for d in days:
        offset = (dt.date.fromisoformat(d['date'])-origin).days
        x, y = 28 + (offset//7)*step, 65 + (offset%7)*step
        body += f'<rect x="{x:.2f}" y="{y:.2f}" width="{step-3:.2f}" height="{step-3:.2f}" rx="2" fill="{palette[min(4,d["level"])]}"><title>{d["date"]}: {d["count"]} contributions</title></rect>'
    # Decorative snake follows the calendar; contribution colors remain unchanged.
    points = []
    for row in range(7):
        cols = range(weeks) if row % 2 == 0 else reversed(range(weeks))
        points.extend(f'{28+c*step+(step-3)/2:.1f},{65+row*step+(step-3)/2:.1f}' for c in cols)
    body += f'<polyline class="snake" points="{" ".join(points)}" fill="none" stroke="#c4b5fd" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" pathLength="1000" stroke-dasharray="8 992" opacity="0.9"/>'
    body += text(28, 192, f'{days[0]["date"]} — {days[-1]["date"]} · {sum(d["count"]>0 for d in days)} active days', 13)
    body += text(28, 217, 'Actual GitHub calendar · animated trail is decorative', 12)
    result['activity.svg'] = svg('GitHub contribution calendar with a decorative animated snake trail', 238, body)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot-dir', type=Path)
    args = parser.parse_args()
    if args.snapshot_dir:
        p = args.snapshot_dir
        user, repos = json.loads((p/'user.data').read_text()), json.loads((p/'repos.data').read_text())
        calendar, languages = (p/'calendar.data').read_text(), json.loads((p/'languages.json').read_text())
    else:
        user = json.loads(fetch(f'https://api.github.com/users/{USER}'))
        repos, page = [], 1
        while True:
            batch = json.loads(fetch(f'https://api.github.com/users/{USER}/repos?per_page=100&page={page}'))
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        languages = {r['name']: json.loads(fetch(r['languages_url'])) for r in repos if not r['fork']}
        calendar = fetch(f'https://github.com/users/{USER}/contributions')
    owned = {r['name'] for r in repos if not r['fork']}
    if set(languages) != owned:
        raise ValueError('Missing repository language data; keeping previous assets')
    c = Calendar()
    c.feed(calendar)
    rendered = render(user, repos, languages, c.days())
    ASSETS.mkdir(exist_ok=True)
    for name, content in rendered.items():
        (ASSETS/name).write_text(content+'\n')
    print('Updated stats, languages and contribution calendar from public GitHub data.')


if __name__ == '__main__':
    main()
