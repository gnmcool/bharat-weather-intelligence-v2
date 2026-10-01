# PREVIEW BRANCH ONLY (preview/farmer-languages) — never merge into main.
# One Vercel preview deployment that serves, on a single origin:
#   /api/v2/*  the V2 API, unchanged (app.main)
#   /api/v1/*  read-only GET pass-through to CORE's public API (CORE's CORS admits only the live site's origin;
#              CORE itself is not changed)
#   /*         the V2 website build from this branch (api-v2/site, built with same-origin API bases)
# Vercel's deployment protection keeps preview URLs behind the owner's Vercel login.
import httpx
from fastapi import Request, Response
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.main import app

app.router.routes = [r for r in app.router.routes if getattr(r, "path", None) != "/"]
_client = httpx.AsyncClient(timeout=httpx.Timeout(90.0), follow_redirects=True)


@app.get("/api/v1/{path:path}")
async def core_passthrough(path: str, request: Request) -> Response:
    r = await _client.get(f"{settings.core_api_base}/{path}", params=request.query_params)
    return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type"),
                    headers={"cache-control": r.headers.get("cache-control", "no-store")})


app.mount("/", StaticFiles(directory="site", html=True), name="site")
