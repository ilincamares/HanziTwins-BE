import os
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import routes_quiz, routes_user, routes_progress
from database.connection import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="HanziTwins API", lifespan=lifespan)

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

app.include_router(routes_quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(routes_user.router, prefix="/api/users", tags=["users"])
app.include_router(routes_progress.router, prefix="/api/progress", tags=["progress"])

@app.get("/")
def read_root():
    return {"message": "Server is running"}


