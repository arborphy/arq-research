import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

app = FastAPI(title="Arborphy Co-Occurrence Explorer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from webapp.backend.routers.co_occurrence import router as co_occurrence_router  # noqa: E402
from webapp.backend.routers.geo import router as geo_router  # noqa: E402
from webapp.backend.routers.features import router as features_router  # noqa: E402
from webapp.backend.routers.debug import router as debug_router  # noqa: E402
from webapp.backend.routers.predicates import router as predicates_router  # noqa: E402

app.include_router(co_occurrence_router, prefix="/api")
app.include_router(geo_router, prefix="/api")
app.include_router(features_router, prefix="/api")
app.include_router(debug_router, prefix="/api")
app.include_router(predicates_router, prefix="/api")
