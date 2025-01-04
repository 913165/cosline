# main.py
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
from app.controllers.api_controller import router as vector_store_router
from app.controllers.payload_controller import router as payload_router

# Define root directories
ROOT_DIR = Path(__file__).parent
COLLECTIONS_DIR = ROOT_DIR / "collections"
CONFIG_DIR = ROOT_DIR / "config"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create necessary directories
    COLLECTIONS_DIR.mkdir(exist_ok=True)
    print(f"Collections directory ensured at: {COLLECTIONS_DIR}")

    CONFIG_DIR.mkdir(exist_ok=True)
    print(f"Config directory ensured at: {CONFIG_DIR}")

    yield  # Server is running

    # Shutdown
    print("Shutting down the application...")

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Include the router
app.include_router(vector_store_router)
app.include_router(payload_router)

@app.get("/")
async def root():
    return {
        "status": "OK",
        "message": "Vector Database2 API is running",
        "collections_path": str(COLLECTIONS_DIR),
        "config_path": str(CONFIG_DIR)
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # Path to your app instance
        host="0.0.0.0",  # Host address (0.0.0.0 allows external access)
        port=8000,  # Port number
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info"  # Logging level
    )