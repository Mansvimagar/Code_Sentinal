# CodeSentinel API

FastAPI serving and GitHub-App integration for the supplied `codesentinel_model` black-box package. It does not alter or duplicate model code.

## Layout

`app/api` exposes HTTP endpoints; `app/services` parses diffs and orchestrates scans; `app/github` verifies webhooks and calls GitHub; `app/db` holds SQLAlchemy models; `alembic` is the only source of schema DDL.

## Run locally

The supplied archive has been unpacked beside this directory as `../codesentinel-model`, so the Compose build installs it directly.

```powershell
cd codesentinel-api
Copy-Item .env.example .env
docker compose up --build
```

Open `http://localhost:8000/docs`. Compose runs `alembic upgrade head` before starting the API. To use a managed Postgres later, set `DATABASE_URL` to its SQLAlchemy psycopg URL; no host is hardcoded in application code.

For non-Docker development, install both packages and migrate:

```powershell
pip install -e ../codesentinel-model
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
pytest
```

## Endpoints

- `POST /score-file` accepts `code_snippet` and optional `language`.
- `POST /analyze-pr` accepts `repo`, `pr_number`, and either a unified `diff` or an `installation_id` to fetch it from GitHub.
- `GET /history` supports `repo`, `severity`, `date_from`, `date_to`, `page`, and `page_size`. Set `REQUIRE_DASHBOARD_AUTH=true` to require an HS256 bearer JWT signed with `JWT_SECRET`.
- `POST /webhooks/github` accepts GitHub `pull_request` events for `opened`, `synchronize`, and `reopened`.

## GitHub App setup

Set `WEBHOOK_SECRET`, `GITHUB_APP_ID`, and `GITHUB_PRIVATE_KEY` (newlines may be written as `\\n`). Configure the webhook URL as `/webhooks/github`, subscribe to Pull requests, and grant the GitHub App **Pull requests: Read**, **Checks: Read & write**, and **Issues: Read & write** permissions. Relevant webhooks fetch the PR diff, persist the scan, create a check run (`failure` for high/critical), and post a concise PR comment.

## Tests

`pytest` covers endpoint success/validation paths, signature verification, a clean Alembic migration, and an end-to-end diff scan with `model_predict` mocked. The real model is never reimplemented or fine-tuned here.
