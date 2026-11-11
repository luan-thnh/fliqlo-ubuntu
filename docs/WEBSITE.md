# Website / GitHub Pages

**Public address:** https://luan-thnh.github.io/fliqlo-ubuntu/

The repository is configured to publish GitHub Pages from the `main` branch's `/docs` folder. Its automatic **pages build and deployment** workflow is managed by GitHub.

## Source and publishing

- Source of truth: `website/index.html`, `website/styles.css`, `website/app.js`, `website/favicon.svg`.
- Published files: `docs/index.html`, `docs/styles.css`, `docs/app.js`, `docs/favicon.svg`.
- Real image assets: `docs/assets/*.png` (actual project renderer outputs and GTK screenshots; no external stock media).

Run this when changing the website or `VERSION`:

```bash
python3 scripts/build-website.py --sync-docs
git add website docs/index.html docs/styles.css docs/app.js docs/favicon.svg docs/.nojekyll
git commit -m "site: update landing page"
git push
```

GitHub automatically rebuilds and publishes `/docs` after a branch push. The separate `.github/workflows/pages.yml` **validates** that the website source and published files are synchronized, and uploads a ZIP-like Actions artifact for review. It is not itself responsible for deploying Pages.

## Preview locally

```bash
python3 scripts/build-website.py
python3 -m http.server 8000 --directory _site
```

Browse to http://localhost:8000.

The builder injects the current release from `VERSION`, validates internal asset links and HTML anchors, then copies checked-in clock and Settings images. No Node build chain or npm packages are required.

## First-time GitHub setup

This repository has been observed using the branch publishing source **main/docs**. If Pages is disabled later, open **Settings → Pages**, select **Deploy from a branch**, branch **main**, folder **/docs**, and save. Do not select the GitHub Actions source unless also replacing the current branch deployment configuration.
