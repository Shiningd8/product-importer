from fastapi import FastAPI

app = FastAPI()

# setting up the root route for testing the API :) 
@app.get("/")
def root():
    return {"message": "Product Importer API is running"}

# setting up the health route for testing the API 
@app.get("/health")
def health():
    return {"status": "ok"}


