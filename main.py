import os

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes_quiz import router as quiz_router

app = FastAPI(title="HanziTwins API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Server is running"}

app.include_router(quiz_router, prefix="/api/quiz", tags=["Quiz Generation"])

