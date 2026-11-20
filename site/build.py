#!/usr/bin/env python3
"""Build the public findings site from this repository.

Standard library only. Reads README.md, docs/*.md and a few results/*.json,
extracts the tables the site shows, scrubs anything that identifies the trial
org, and writes a static site to _site/ (or the folder given as argv[1]).

The build fails if anything that looks like a credential is left in the output.
Run locally:  python3 site/build.py && python3 -m http.server -d _site 8000
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site" / "src"
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "_site"
REPO_URL = "https://github.com/mondweep/kongai-evaluation"

# ---------------------------------------------------------------- scrubbing
SCRUB = [
    # Konnect entity, org and control-plane IDs
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "[redacted-id]"),
    # Our gateway and portal hostnames
    (re.compile(r"https?://[a-z0-9]+\.eu\.serverless\.gateways\.konggateway\.com", re.I), "https://YOUR-GATEWAY.example"),
    (re.compile(r"https?://[a-z0-9]+\.eu\.kongportals\.com", re.I), "https://YOUR-PORTAL.example"),
    (re.compile(r"\b[a-z0-9]{10,}\.eu\.(serverless\.gateways\.konggateway|kongportals)\.com", re.I), "[redacted-host]"),
    # Private Claude Docs links (not public)
    (re.compile(r"(Living [a-z ]*(?:doc|version)[^:\n]*:\s*)?https://claude\.ai/artifact/[A-Za-z0-9]+", re.I), ""),
    # Internal names
    (re.compile(r"serverless-api-gateway-demo"), "the serverless control plane"),
    (re.compile(r"Wipro Demo Portal"), "the demo portal"),
    (re.compile(r"wipro-demo-portal"), "demo-portal"),
    # Email addresses (keep example.* test data)
    (re.compile(r"\b[A-Za-z0-9._%+-]+@(?!(?:[a-z0-9-]+\.)*example\b)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b"), "[email removed]"),
]

SECRET = re.compile(
    r"kpat_[A-Za-z0-9]{20,}|spat_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9_-]{24,}"
    r"|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY"
)


def scrub(text: str) -> str:
    for pat, rep in SCRUB:
        text = pat.sub(rep, text)
    return text


# ---------------------------------------------------------------- markdown helpers
def md_tables(md: str):
    """Yield (heading, rows) for each pipe table; rows are lists of cell strings."""
    heading, lines, out = "", md.splitlines(), []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*:?-{3,}", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|\s*:?-{3,}", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append((heading, rows))
            continue
        i += 1
    return out


def find_table(md, first_header):
    for heading, rows in md_tables(md):
        if rows and rows[0][0].lower() == first_header.lower():
            return heading, rows
    raise SystemExit(f"build: table starting with '{first_header}' not found")


def plain(cell: str) -> str:
    """Markdown cell to plain text (keep inline code as text)."""
    cell = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cell)
    cell = cell.replace("**", "").replace("`", "")
    return cell.strip()


def links(cell: str):
    return [{"text": t, "doc": Path(h.split("#")[0]).name} for t, h in re.findall(r"\[([^\]]+)\]\(([^)]+\.md)[^)]*\)", cell)]


def strip_bold_lead(s):
    m = re.match(r"\*\*(.+?)\*\*\s*(.*)", s)
    return (m.group(1), m.group(2)) if m else ("", s)


# ---------------------------------------------------------------- extraction
def build_data():
    readme = (ROOT / "README.md").read_text()
    report = (ROOT / "docs" / "report.md").read_text()
    coverage_md = (ROOT / "docs" / "feature-coverage.md").read_text()

    # Five risk verdicts (report.md summary table)
    _, rows = find_table(report, "Risk")
    risks = []
    for r in rows[1:]:
        name = re.sub(r"^\d+\.\s*", "", plain(r[0]))
        risks.append({"risk": name, "verdict": plain(r[1]), "summary": plain(r[2])})

    # Evaluations overview (README "What we evaluated")
    _, rows = find_table(readme, "Evaluation")
    evaluations = [
        {"name": plain(r[0]), "docs": [l["doc"] for l in links(r[0])], "question": plain(r[1]), "answer": plain(r[2])}
        for r in rows[1:]
    ]

    # Coverage matrix
    _, rows = find_table(coverage_md, "Area")
    coverage = []
    for r in rows[1:]:
        status = plain(r[2])
        key = ("hands-on" if status.lower().startswith("hands-on") else
               "partial" if status.lower().startswith("partial") else
               "seen" if status.lower().startswith("seen") else "cant")
        coverage.append({"area": plain(r[0]), "feature": plain(r[1]), "status": status, "key": key,
                         "evidence": plain(r[3]), "docs": [l["doc"] for l in links(r[4])] if len(r) > 4 else []})
    m = re.search(r"(\d+) of the (\d+) Konnect menu items", coverage_md)
    tested, total = (int(m.group(1)), int(m.group(2))) if m else (None, len(coverage))

    # Numbered headline findings from README
    findings, section = [], ""
    for line in readme.split("## Headline findings", 1)[1].split("\n## ", 1)[0].splitlines():
        if line.startswith("### "):
            section = line[4:].strip()
        mm = re.match(r"^(\d+)\.\s+(.*)", line)
        if mm:
            title, body = strip_bold_lead(mm.group(2))
            findings.append({"n": int(mm.group(1)), "section": section, "title": plain(title),
                             "body": plain(body), "docs": [l["doc"] for l in links(body)]})

    # Virtual models: raw results
    vm = json.loads((ROOT / "results" / "vm-switch-fallback.json").read_text())
    vm_runs = {k: [{"status": r.get("status"), "model": r.get("x_kong_llm_model")} for r in v]
               for k, v in vm.items() if isinstance(v, list)}
    cap = json.loads((ROOT / "results" / "vm-per-model-cost-cap.json").read_text())
    vm_cap = [{"i": r[0] + 1, "status": r[1], "model": r[2]} for r in cap]

    # MetaLLM call table
    metallm_md = (ROOT / "docs" / "metallm-findings.md").read_text()
    _, rows = find_table(metallm_md, "#")
    metallm = [dict(zip(["n", "requested", "prompt", "result", "tier", "latency", "tokens", "price"],
                        [plain(c) for c in r])) for r in rows[1:]]

    # Write-ups library
    library = []
    for p in sorted((ROOT / "docs").glob("*.md")):
        text = p.read_text()
        title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("# ")), p.stem)
        library.append({"file": p.name, "title": title})

    return {
        "repo": REPO_URL,
        "risks": risks,
        "evaluations": evaluations,
        "coverage": {"tested": tested, "total": total, "items": coverage},
        "findings": findings,
        "virtualModels": {"runs": vm_runs, "costCap": vm_cap},
        "metallm": metallm,
        "library": library,
    }


# ---------------------------------------------------------------- build
def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)
    (OUT / "docs").mkdir(exist_ok=True)

    data = build_data()
    curated = json.loads((SRC / "content.json").read_text())
    data["content"] = curated
    (OUT / "content.json").unlink()

    for p in (ROOT / "docs").glob("*.md"):
        (OUT / "docs" / p.name).write_text(scrub(p.read_text()))
    (OUT / "data.json").write_text(scrub(json.dumps(data, indent=1, ensure_ascii=False)))
    (OUT / ".nojekyll").write_text("")

    # Gate: nothing credential-like, no IDs, no internal hosts
    bad = []
    for f in OUT.rglob("*"):
        if f.is_file():
            t = f.read_text(errors="ignore")
            for pat in [SECRET] + [p for p, _ in SCRUB[:4]]:
                if pat.search(t):
                    bad.append(f"{f.relative_to(OUT)}: {pat.search(t).group(0)[:12]}...")
    if bad:
        print("build: refusing to publish, sensitive-looking data found:\n  " + "\n  ".join(bad))
        sys.exit(1)
    print(f"build: wrote {OUT} ({len(data['coverage']['items'])} coverage items, "
          f"{len(data['findings'])} findings, {len(data['library'])} write-ups)")


if __name__ == "__main__":
    main()
