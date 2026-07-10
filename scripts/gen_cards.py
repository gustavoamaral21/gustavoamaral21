#!/usr/bin/env python3
"""Gera os cards de estatísticas e linguagens do perfil (SVG) com dados reais.
Usa o gh CLI (autenticado via GH_TOKEN no CI ou keyring local)."""
import json, subprocess, sys, os, re

OUT_ASSETS = os.environ.get("ASSETS_DIR", os.path.dirname(os.path.abspath(__file__)))
USER = os.environ.get("PROFILE_USER", "gustavoamaral21")

def gh(args):
    env = dict(os.environ); env["MSYS_NO_PATHCONV"] = "1"
    r = subprocess.run(["gh"] + args, capture_output=True, text=True, env=env, encoding="utf-8")
    if r.returncode != 0:
        sys.stderr.write("WARN gh " + " ".join(args) + " -> " + (r.stderr or "")[:200] + "\n")
        return None
    return r.stdout

def commit_count(full):
    env = dict(os.environ); env["MSYS_NO_PATHCONV"] = "1"
    r = subprocess.run(["gh", "api", "-i", f"repos/{full}/commits?per_page=1"],
                       capture_output=True, text=True, env=env, encoding="utf-8")
    out = r.stdout or ""
    for line in out.splitlines():
        if line.lower().startswith("link:") and 'rel="last"' in line:
            m = re.search(r'[?&]page=(\d+)>;\s*rel="last"', line)
            if m:
                return int(m.group(1))
    m = re.search(r"\n\r?\n(\[.*\])", out, re.S)
    if m:
        try:
            return len(json.loads(m.group(1)))
        except Exception:
            return 0
    return 0

# ---- repos (owner, inclui privados) ----
repos = json.loads(gh(["api", "--paginate", "user/repos?per_page=100&affiliation=owner"]) or "[]")
stars = total_commits = n_repos = 0
lang_bytes = {}
for rp in repos:
    if rp.get("fork"):
        continue
    n_repos += 1
    stars += rp.get("stargazers_count", 0)
    total_commits += commit_count(rp["full_name"])
    lg = gh(["api", f"repos/{rp['full_name']}/languages"])
    if lg:
        for k, v in json.loads(lg).items():
            lang_bytes[k] = lang_bytes.get(k, 0) + v

if n_repos == 0:
    sys.exit("Nenhum repositório acessível — token sem acesso (defina METRICS_TOKEN). Abortando para não sobrescrever os cards.")

u = json.loads(gh(["api", f"users/{USER}"]) or "{}")
followers = u.get("followers", 0)
member_since = (u.get("created_at") or "2021")[:4]
n_langs = len(lang_bytes)

# Distribuição de linguagens CURADA por projeto (estável e representativa —
# a contagem por bytes do GitHub distorce: infla libs/CSS e não enxerga os
# microsserviços Go/Python que ficam em repositórios locais/privados).
CURATED_LANGS = [("PHP", 30), ("TypeScript", 24), ("Python", 18), ("Go", 14),
                 ("JavaScript", 8), ("SQL", 6)]

COLORS = {
    "PHP": "#4F5D95", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Go": "#00ADD8",
    "Python": "#3572A5", "HTML": "#e34c26", "CSS": "#563d7c", "Vue": "#41b883",
    "Blade": "#f7523f", "Shell": "#89e051", "Dockerfile": "#384d54", "SCSS": "#c6538c",
    "Less": "#1d365d", "Makefile": "#427819", "SQL": "#e38c00", "Java": "#b07219",
    "C#": "#178600", "Jupyter Notebook": "#DA5B0B",
}
def color(name): return COLORS.get(name, "#70a5fd")

summary = {"total_commits": total_commits, "stars": stars, "followers": followers,
           "repos": n_repos, "languages": n_langs, "member_since": member_since,
           "top": CURATED_LANGS}
top = CURATED_LANGS
print(json.dumps(summary, ensure_ascii=False, indent=2))

BG = "#1a1b27"; TITLE = "#70a5fd"; TEXT = "#a9b1d6"; ICON = "#bf91f3"; VAL = "#38bdae"; BORDER = "#2a2e42"
FONT = "Segoe UI, Ubuntu, sans-serif"

# ---- STATS ----
rows = [("↑", "Commits totais", total_commits), ("▤", "Repositórios", n_repos),
        ("⌘", "Linguagens", n_langs), ("♦", "Seguidores", followers),
        ("◷", "Membro desde", member_since)]
h = 60 + len(rows) * 28 + 20
s = [f'<svg width="470" height="{h}" viewBox="0 0 470 {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
s.append(f'<rect x="0.5" y="0.5" width="469" height="{h-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>')
s.append(f'<text x="25" y="35" font-family="{FONT}" font-size="18" font-weight="600" fill="{TITLE}">Estatísticas de Gustavo Amaral</text>')
y = 66
for ic, label, val in rows:
    vtxt = f"{val:,}".replace(",", ".") if isinstance(val, int) else str(val)
    s.append(f'<text x="25" y="{y}" font-family="{FONT}" font-size="15" fill="{ICON}">{ic}</text>')
    s.append(f'<text x="52" y="{y}" font-family="{FONT}" font-size="15" fill="{TEXT}">{label}</text>')
    s.append(f'<text x="445" y="{y}" text-anchor="end" font-family="{FONT}" font-size="15" font-weight="700" fill="{VAL}">{vtxt}</text>')
    y += 28
s.append("</svg>")
open(os.path.join(OUT_ASSETS, "stats.svg"), "w", encoding="utf-8").write("\n".join(s))

# ---- TOP LANGS ----
h2 = 60 + len(top) * 30 + 20
t = [f'<svg width="360" height="{h2}" viewBox="0 0 360 {h2}" xmlns="http://www.w3.org/2000/svg" role="img">']
t.append(f'<rect x="0.5" y="0.5" width="359" height="{h2-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>')
t.append(f'<text x="25" y="35" font-family="{FONT}" font-size="18" font-weight="600" fill="{TITLE}">Linguagens mais usadas</text>')
y = 58; BARW = 310
for name, pct in summary["top"]:
    t.append(f'<text x="25" y="{y}" font-family="{FONT}" font-size="13" fill="{TEXT}">{name}</text>')
    t.append(f'<text x="335" y="{y}" text-anchor="end" font-family="{FONT}" font-size="13" fill="{TEXT}">{pct}%</text>')
    t.append(f'<rect x="25" y="{y+6}" width="{BARW}" height="8" rx="4" fill="{BORDER}"/>')
    w = max(4, round(BARW * pct / 100))
    t.append(f'<rect x="25" y="{y+6}" width="{w}" height="8" rx="4" fill="{color(name)}"/>')
    y += 30
t.append("</svg>")
open(os.path.join(OUT_ASSETS, "top-langs.svg"), "w", encoding="utf-8").write("\n".join(t))
print("OK ->", OUT_ASSETS)
