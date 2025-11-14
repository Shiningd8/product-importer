from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import products, upload, webhooks

app = FastAPI(title="Product Importer API", version="1.0.0")

# Serve static files - the frontend UI
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers - connecting all the API pieces together
app.include_router(products.router)
app.include_router(upload.router)
app.include_router(webhooks.router)

@app.get("/")
async def root():
    """Serve the main UI page."""
    return FileResponse("app/static/index.html")

@app.get("/health")
def health():
    """Health check endpoint - because even APIs need regular checkups."""
    return {"status": "ok"}

