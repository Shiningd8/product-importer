from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Product Importer API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
