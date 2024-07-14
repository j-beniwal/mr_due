from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, documents, inference
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(inference.router, prefix="/api/inference", tags=["inference"])

@app.get("/")
async def root():
    return {"message": "Welcome to Mr.due API"}