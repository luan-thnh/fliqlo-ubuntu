# Landing page — GitHub Pages

Source: `website/index.html`, `website/styles.css`, `website/app.js`.

Live URL once GitHub Pages is enabled:
**https://luan-thnh.github.io/fliqlo-ubuntu/**

## Build locally

```bash
python3 scripts/build-website.py
python3 -m http.server 8000 --directory _site
```

Open `http://localhost:8000` to preview.

This is a dependency-free static website. The build reads `VERSION`, renders it into the page, and copies actual project-generated clock theme images and native GTK screenshots from `docs/assets` into `_site/assets`. It validates image links and internal anchor targets.

## GitHub Pages publishing

The workflow `.github/workflows/pages.yml` runs on updates to the site, project version, and demo images, and deploys via `actions/upload-pages-artifact` + `actions/deploy-pages`.

**First-time setup, if the deploy job reports Pages is not enabled:**

1. Open **GitHub repository → Settings → Pages**.
2. Under **Build and deployment → Source**, select **GitHub Actions**.
3. Rerun the **Website · GitHub Pages** workflow from **Actions**.

GitHub App connector permissions here do not expose an action for changing repository Pages settings, and GitHub's `configure-pages` action cannot enable Pages automatically using the default `GITHUB_TOKEN`; a different token with Pages/admin permissions would be needed. Do not publish a token in source control.

The existing `build.yml` for Debian/extension releases is kept separate so website changes do not require publishing a new software version. The Download button links to the `.deb` from the release matching `VERSION`.

For production, keep Pages deployments limited to the `main` branch and ensure HTTPS is enabled (GitHub-hosted domains use HTTPS by default).
