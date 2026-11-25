"""Build a weekly organization activity chart from public default-branch commits."""
from collections import Counter
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "weekly-activity.svg"


def render(dates, today):
    start = today - timedelta(days=today.weekday() + 77)
    counts = [0] * 12
    for stamp in dates:
        day = datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(timezone.utc).date()
        if start <= day <= today:
            counts[(day - start).days // 7] += 1
    peak = max(max(counts), 1)
    points, labels, grid = [], [], []
    for tick in sorted({0, peak // 2, peak}):
        y = 148 - 90 * tick / peak
        grid.append(f'<path d="M42 {y}H722" stroke="#303449"/><text x="30" y="{y+4}" text-anchor="end">{tick}</text>')
    for i, count in enumerate(counts):
        x, y = 42 + 680*i/11, 148 - 90*count/peak
        points.append(f'{x:.1f},{y:.1f}')
        week = start + timedelta(weeks=i)
        labels.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#bf91f3"><title>{week}: {count} commits</title></circle><text x="{x:.1f}" y="172" text-anchor="middle">{week:%d %b}</text>')
    path = "M" + " L".join(points)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="760" height="190" viewBox="0 0 760 190" role="img">
<title>Weekly contributions: {", ".join(map(str, counts))}</title>
<defs><linearGradient id="area" x2="0" y2="1" gradientUnits="objectBoundingBox"><stop stop-color="#70a5fd" stop-opacity=".42"/><stop offset="1" stop-color="#70a5fd" stop-opacity=".04"/></linearGradient></defs>
<rect width="760" height="190" rx="7" fill="#1a1b27"/><g font-family="system-ui,sans-serif" font-size="10" fill="#a9b1d6">
<text x="22" y="30" font-size="18" font-weight="650" fill="#70a5fd">TCC PENS Contribution Graph</text>
<text x="722" y="30" font-size="12" text-anchor="end">{sum(counts)} commits · 12 weeks</text>
{"".join(grid)}<path d="{path} L722,148 H42 Z" fill="url(#area)"/><path d="{path}" fill="none" stroke="#70a5fd" stroke-width="2.5" stroke-linejoin="round"/>
{"".join(labels)}</g></svg>
"""


def render_snake(dates, today):
    start = today - timedelta(days=today.weekday() + 51 * 7)
    daily = Counter(datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).date() for value in dates)
    cells = []
    points = []
    for column in range(52):
        for row in range(7):
            day = start + timedelta(days=column * 7 + row)
            if day > today:
                continue
            count = daily[day]
            x, y = 17 + 14 * column, 18 + 14 * row
            color = "#282e45" if not count else ("#648fd6" if count < 4 else "#9ece6a")
            cells.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{color}"><title>{day}: {count} commits</title></rect>')
            if count:
                points.append((x+5, y+5))
    trail = ""
    if points:
        x, y = points[0]
        path = f"M17 {y} H{x}" + "".join(f" H{x} V{y}" for x, y in points[1:])
        trail = f'<path d="{path}" fill="none" stroke="#c6a0f6" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" pathLength="100" stroke-dasharray="4 100"><animate attributeName="stroke-dashoffset" from="4" to="-100" dur="12s" repeatCount="indefinite"/></path>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="132" viewBox="0 0 760 132"><title>Daily commits from {start} through {today}</title><rect width="760" height="132" rx="8" fill="#171a29"/>{"".join(cells)}{trail}</svg>\n'


if __name__ == "__main__":
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=today.weekday() + 51 * 7)
    dates = []
    for page in json.load(sys.stdin):
        for repo in page:
            if repo["fork"] or repo["visibility"] != "public":
                continue
            endpoint = f'repos/{repo["full_name"]}/commits?per_page=100&since={start}T00:00:00Z'
            result = subprocess.run(["gh", "api", "--paginate", endpoint, "--jq",
                                     ".[].commit.committer.date"], capture_output=True, text=True)
            if result.returncode and "Git Repository is empty" in result.stderr:
                continue
            result.check_returncode()
            dates.extend(result.stdout.splitlines())
    OUTPUT.write_text(render(dates, today), encoding="utf-8")
    OUTPUT.with_name("snake.svg").write_text(render_snake(dates, today), encoding="utf-8")
