from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.api.v1.api import api_router
from app.core.config import settings
from app.database import engine, Base
# Create database tables (Only for SQLite during development/testing)
# For PostgreSQL with Alembic, migrations handle table creation.
if "sqlite" in str(engine.url):
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
def read_root():
    return RedirectResponse(url="/docs")

# Add other configurations like CORS middleware if needed
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], # Adjust in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

