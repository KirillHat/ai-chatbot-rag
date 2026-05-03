# Deployment Templates

One-command deploy on three popular PaaS providers — pick the one your
client already pays for. All three serve the same Docker image, all three
mount a persistent volume for ChromaDB + SQLite + uploads.

## What you need *before* any deploy

1. An Anthropic API key (`https://console.anthropic.com`).
2. A long random `ADMIN_API_TOKEN` (≥ 32 chars). On Render the platform mints one for you.
3. The list of domains the widget will be embedded on — for the `CORS_ORIGINS` env var.

## Railway

```bash
# install once
npm i -g @railway/cli && railway login

# from the project root
railway init
railway up                         # builds the Dockerfile + ships
railway variables --set ANTHROPIC_API_KEY=sk-ant-… \
                  --set ADMIN_API_TOKEN=$(openssl rand -hex 24) \
                  --set CORS_ORIGINS=https://acme.com
railway open                       # opens the deployed URL
```

Railway auto-detects [`deploy/railway.json`](railway.json) and uses our
Dockerfile + `/health` healthcheck.

## Fly.io

```bash
brew install flyctl && fly auth login

# Once-only setup
fly launch --copy-config deploy/fly.toml --no-deploy
fly volumes create chatbot_data --region iad --size 1
fly secrets set ANTHROPIC_API_KEY=sk-ant-… \
                ADMIN_API_TOKEN=$(openssl rand -hex 24)

fly deploy
```

The volume mounts at `/data` so all writes (ChromaDB, SQLite, uploads)
survive deploys. The auto-stop config in `fly.toml` scales to zero when
idle — your bill stays near zero on a low-traffic demo site.

## Render

Push this repo to GitHub, then in the Render dashboard:

1. **New → Blueprint**
2. Pick this repo
3. Render reads [`deploy/render.yaml`](render.yaml), provisions a Docker
   web service + 1 GB persistent disk, and prompts you for
   `ANTHROPIC_API_KEY` (everything else is auto-set).

Total elapsed time: ~3 minutes from "create blueprint" to a public HTTPS
URL with the demo landings live at `/demo/hotel/`, `/demo/law/` and
`/demo/admin/`.

## Heroku-style platforms

A `Procfile` is provided in the repo root (`web: uvicorn ...`). Anything
that respects `Procfile` (Heroku, Dokku, Coolify, Northflank free tier)
should boot the app out of the box. Mount a writable disk at `./data` —
or set `CHROMA_DIR`, `SQLITE_PATH` and `UPLOAD_DIR` to wherever your
platform gives you persistent storage.

## After deploying — the 60-second smoke test

```bash
URL=https://your-app.example.com

# Should report status:"degraded" until you set ANTHROPIC_API_KEY
curl -s "$URL/health" | jq

# Should return the JSON config the widget reads
curl -s "$URL/api/widget/config" | jq

# Should return 401 (admin enabled but no token)
curl -s -o /dev/null -w "%{http_code}\n" "$URL/api/admin/documents"

# With your real token — should return 200 + an empty list
curl -s -H "Authorization: Bearer $ADMIN_API_TOKEN" \
        "$URL/api/admin/documents" | jq
```

Then open `$URL/demo/admin/`, paste your admin token, drop a PDF, and
chat away on `$URL/demo/hotel/`.
