"""
Web routes — Jinja2 pages served by FastAPI.
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
from typing import Optional
import httpx

router = APIRouter(tags=["Web"])
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
_client = httpx.AsyncClient(trust_env=False, base_url=API_BASE, timeout=10.0)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard with stats and recent certificates."""
    resp = await _client.get("/api/v1/certificates", params={"page": 1, "page_size": 5})
    data = resp.json() if resp.status_code == 200 else {"data": [], "total": 0}

    return templates.TemplateResponse(request, "dashboard.html", {
        "certificates": data.get("data", []),
        "total": data.get("total", 0),
    })


@router.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    """Certificate generation form."""
    return templates.TemplateResponse(request, "generate.html", {})


@router.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request, cert_id: Optional[str] = None):
    """Public certificate verification."""
    result = None
    error = None
    if cert_id:
        resp = await _client.get(f"/api/v1/certificates/{cert_id}")
        if resp.status_code == 200:
            result = resp.json().get("data")
        else:
            error = "Certificate not found"

    return templates.TemplateResponse(request, "verify.html", {
        "result": result,
        "error": error,
        "cert_id": cert_id or "",
    })


@router.get("/registry", response_class=HTMLResponse)
async def registry_page(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    track: Optional[str] = None,
):
    """Certificate registry with search, filter, pagination."""
    params = {"page": page, "page_size": page_size}
    if search:
        params["search"] = search
    if track:
        params["track"] = track

    resp = await _client.get("/api/v1/certificates", params=params)
    data = resp.json() if resp.status_code == 200 else {"data": [], "total": 0, "skip": 0, "limit": 20}

    total = data.get("total", 0)
    total_pages = max(1, (total + page_size - 1) // page_size)

    return templates.TemplateResponse(request, "registry.html", {
        "certificates": data.get("data", []),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "search": search or "",
        "track": track or "",
    })


@router.get("/certificates/{cert_id}", response_class=HTMLResponse)
async def certificate_detail(request: Request, cert_id: str):
    """Certificate detail page."""
    resp = await _client.get(f"/api/v1/certificates/{cert_id}")
    if resp.status_code == 200:
        result = resp.json().get("data")
    else:
        return templates.TemplateResponse(request, "verify.html", {
            "result": None,
            "error": "Certificate not found",
            "cert_id": cert_id,
        })

    return templates.TemplateResponse(request, "detail.html", {
        "cert": result,
    })


# ─── HTMX Partials ───

@router.get("/partials/registry-table", response_class=HTMLResponse)
async def registry_table(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    track: Optional[str] = None,
):
    """HTMX partial: certificate table with pagination."""
    params = {"page": page, "page_size": page_size}
    if search:
        params["search"] = search
    if track:
        params["track"] = track

    resp = await _client.get("/api/v1/certificates", params=params)
    data = resp.json() if resp.status_code == 200 else {"data": [], "total": 0}

    total = data.get("total", 0)
    total_pages = max(1, (total + page_size - 1) // page_size)

    return templates.TemplateResponse(request, "partials/cert_table.html", {
        "certificates": data.get("data", []),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "search": search or "",
        "track": track or "",
    })


@router.get("/partials/verify-result", response_class=HTMLResponse)
async def verify_result(request: Request, cert_id: str = ""):
    """HTMX partial: verify certificate result."""
    result = None
    error = None
    if cert_id:
        resp = await _client.get(f"/api/v1/certificates/{cert_id}")
        if resp.status_code == 200:
            result = resp.json().get("data")
        else:
            error = "Certificate not found"

    return templates.TemplateResponse(request, "partials/verify_result.html", {
        "result": result,
        "error": error,
    })


@router.post("/partials/generate-result", response_class=HTMLResponse)
async def generate_result(
    request: Request,
    student_name: str = Form(...),
    course_track: str = Form(...),
    level: str = Form(...),
    issue_date: str = Form(...),
    branch: str = Form(...),
    instructor: str = Form(""),
    director: str = Form(""),
):
    """HTMX partial: generate certificate via API and return result."""
    payload = {
        "student_name": student_name,
        "course_track": course_track,
        "level": level,
        "issue_date": issue_date,
        "branch": branch,
    }
    if instructor:
        payload["instructor"] = instructor
    if director:
        payload["director"] = director

    cert = None
    error = None
    resp = await _client.post("/api/v1/certificates", json=payload)
    if resp.status_code == 200:
        cert = resp.json().get("data")
    else:
        detail = resp.json().get("detail")
        if isinstance(detail, list):
            error = "; ".join(str(e.get("msg", e)) for e in detail)
        elif isinstance(detail, str):
            error = detail
        else:
            error = "Failed to generate certificate"

    return templates.TemplateResponse(request, "partials/generate_result.html", {
        "cert": cert,
        "success": cert is not None,
        "error": error,
    })


TRACKS = [
    ("html", "HTML"),
    ("css", "CSS"),
    ("javascript", "JavaScript"),
    ("python", "Python"),
    ("advanced", "Advanced"),
    ("problem_solving", "Problem Solving"),
    ("robotics-wedo", "Robotics WeDo 2.0"),
    ("robotics-spike-essential", "Robotics SPIKE Essential"),
    ("robotics-spike-prime", "Robotics SPIKE Prime"),
    ("robotics-ev3", "Robotics EV3"),
    ("robotics-arduino", "Robotics Arduino"),
    ("scratch", "Scratch"),
    ("scratch-jr", "Scratch Jr"),
]

LEVELS = [
    "Level 1 — Junior",
    "Level 2 — Intermediate",
    "Level 3 — Advanced",
]
