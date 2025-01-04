from fastapi import FastAPI
from .controllers import router

app = FastAPI(title="Vector Database API")

# Include the router
app.include_router(router)