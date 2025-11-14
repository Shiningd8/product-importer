from fastapi import FastAPI
from app.api.routes import products

app = FastAPI(title="Product Importer API", version="1.0.0")

# Include routers - connecting all the API pieces together
app.include_router(products.router)

@app.get("/")
def root():
    """Welcome endpoint - your first stop in the API journey."""
    return {"message": "Product Importer API is running"}

@app.get("/health")
def health():
    """Health check endpoint - because even APIs need regular checkups."""
    return {"status": "ok"}

