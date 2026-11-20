# Findings site

The public, interactive site at https://mondweep.github.io/kongai-evaluation/ is generated from this repository, so it stays in sync with the write-ups.

- `build.py` reads `README.md`, `docs/*.md` and a few `results/*.json`, extracts the risk verdicts, coverage matrix, headline findings, virtual-model runs and MetaLLM calls, and writes a static site to `_site/`.
- `src/content.json` holds the curated chart numbers and wording. Each block names the write-up it comes from. Update it when a headline number changes.
- `src/` is plain HTML, CSS and JavaScript with no build tooling. `src/vendor/` holds marked 12.0.2 (MIT) and DOMPurify 3.1.6 (Apache-2.0 or MPL-2.0) for the write-up reader.
- The build scrubs IDs, internal hostnames, private doc links and emails from everything it publishes, and **fails** if anything that looks like a token or key remains.
- `.github/workflows/pages.yml` builds on every pull request (as a check) and publishes to GitHub Pages on every merge to `main`.

Preview locally:

```sh
python3 site/build.py && python3 -m http.server -d _site 8000
```
