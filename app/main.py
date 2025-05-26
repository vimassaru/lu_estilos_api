from fastapi import FastAPI
from app.api.v1.api import api_router
from app.core.config import settings
from app.database import engine, Base
import uvicorn # Import uvicorn

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
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

# Add other configurations like CORS middleware if needed
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], # Adjust in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Block to run Uvicorn directly using python app/main.py
if __name__ == "__main__":
    # Note: Running this way might cause import issues depending on how you run it.
    # The recommended way is: uvicorn app.main:app --reload --port 8008
    # However, this block allows direct execution.
    # The app string "app.main:app" tells uvicorn where to find the FastAPI instance.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8008, reload=True)

