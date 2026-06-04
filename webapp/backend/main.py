import logging
import os
import sys
from pathlib import Path

logging.getLogger("relationalai").setLevel(logging.WARNING)
logging.getLogger("v0.relationalai").setLevel(logging.WARNING)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

app = FastAPI(title="Arborphy Co-Occurrence Explorer")

_origins = os.environ.get(
    "CORS_ORIGINS",
    # Default: all three Vite dev servers in the arborphy stack.
    # arq-visualization=5173, arq-research/webapp/frontend=5174, arq-mobile=5176
    "http://localhost:5173,http://localhost:5174,http://localhost:5176",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

from webapp.backend.routers.co_occurrence import router as co_occurrence_router  # noqa: E402
from webapp.backend.routers.geo import router as geo_router  # noqa: E402
from webapp.backend.routers.features import router as features_router  # noqa: E402
from webapp.backend.routers.debug import router as debug_router  # noqa: E402
from webapp.backend.routers.predicates import router as predicates_router  # noqa: E402
from webapp.backend.routers.ecosites import router as ecosites_router  # noqa: E402
from webapp.backend.routers.trails import router as trails_router  # noqa: E402
from webapp.backend.routers.gobotany import router as gobotany_router  # noqa: E402
from webapp.backend.routers.observations import router as observations_router  # noqa: E402
from webapp.backend.routers.field import router as field_router, media_root  # noqa: E402
from webapp.backend.routers.quest_contracts import router as quest_contracts_router  # noqa: E402

app.include_router(co_occurrence_router, prefix="/api")
app.include_router(geo_router, prefix="/api")
app.include_router(features_router, prefix="/api")
app.include_router(debug_router, prefix="/api")
app.include_router(predicates_router, prefix="/api")
app.include_router(ecosites_router, prefix="/api")
app.include_router(trails_router, prefix="/api")
app.include_router(gobotany_router, prefix="/api")
app.include_router(observations_router, prefix="/api")
app.include_router(field_router, prefix="/api")
app.include_router(quest_contracts_router, prefix="/api")

# Serve uploaded field photos. The directory is created lazily on first
# upload; ensure it exists now so the mount has something to point at.
_media = media_root()
_media.mkdir(parents=True, exist_ok=True)
app.mount("/api/field/media", StaticFiles(directory=str(_media)), name="field-media")
