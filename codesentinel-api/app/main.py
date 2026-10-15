from __future__ import annotations
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.api.routes import router
from app.db.session import SessionLocal, get_db
from app.github.client import GitHubClient
from app.github.webhook import verify_signature
from app.services.scanner import scan_diff, worst_severity

app = FastAPI(title="CodeSentinel API", version="0.1.0", description="AI-powered CI/CD vulnerability gatekeeper")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")

def process_pull_request(payload: dict) -> None:
    installation = payload["installation"]["id"]; pull = payload["pull_request"]; repo_data = payload["repository"]
    repo_name = repo_data["full_name"]; client = GitHubClient(installation); db = SessionLocal()
    try:
        diff = client.get_pr_diff(repo_name, pull["number"])
        scan = scan_diff(db, repo_name=repo_name, pr_number=pull["number"], diff=diff, commit_sha=pull["head"]["sha"], github_repo_id=repo_data.get("id"))
        severity = worst_severity(scan); count = len(scan.findings)
        conclusion = "failure" if severity in {"high", "critical"} else "neutral" if severity else "success"
        summary = f"{count} finding(s); worst severity: {severity or 'none'}."
        client.post_check(repo_name, pull["head"]["sha"], conclusion, summary)
        client.post_comment(repo_name, pull["number"], f"## CodeSentinel\n{summary}")
    finally: db.close()

@app.post("/webhooks/github", status_code=202)
async def github_webhook(request: Request, tasks: BackgroundTasks) -> dict[str, str]:
    raw = await request.body(); verify_signature(raw, request.headers.get("X-Hub-Signature-256"))
    payload = await request.json()
    if request.headers.get("X-GitHub-Event") != "pull_request" or payload.get("action") not in {"opened", "synchronize", "reopened"}: return {"status": "ignored"}
    if not payload.get("installation"): raise HTTPException(422, "GitHub App installation is required")
    tasks.add_task(process_pull_request, payload)
    return {"status": "accepted"}

@app.get("/health")
def health() -> dict[str, str]: return {"status": "ok"}
