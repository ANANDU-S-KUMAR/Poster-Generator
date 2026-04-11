import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from starlette.staticfiles import StaticFiles
from starlette.types import Scope, Receive, Send

import uuid
from poster import PosterGenerator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

jobs: dict = {}
executor = ThreadPoolExecutor(max_workers=4)


class PosterRequest(BaseModel):
    title: str
    description: str
    genre: str = None
    episodes: int = 2


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    best_img: str | None = None
    other_img: list[str] | None = None
    error: str | None = None


def run_poster_generator(job_id: str, request: PosterRequest):
    try:
        jobs[job_id]["status"] = "running"
        generator = PosterGenerator(
            title=request.title,
            description=request.description,
            genre=request.genre,
            episodes=request.episodes,
        )
        best_img,other_img = generator.generate()
        jobs[job_id].update(
            {
                "status": "completed",
                "best_img": best_img,
                "other_img": other_img
            }
        )
    except Exception as e:
        jobs[job_id].update(
            {
                "status": "failed",
                "error": str(e),
            }
        )


@app.post("/generate_poster", response_model=JobResponse)
async def generate_poster(request: PosterRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "best_img": None,
        "other_img": [],
        "error": None,
    }

    loop = asyncio.get_running_loop()
    loop.run_in_executor(executor, run_poster_generator, job_id, request)
    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Job started. Call /status/{job_id} to check status.",
    )

@app.get("/status/{job_id}", response_model=JobStatusResponse)
def get_status(job_id: str):
    if job_id not in jobs:
        return JobStatusResponse(job_id=job_id, status="not found")
    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        best_img=f"/output/{job['best_img']}" if job["best_img"] else None,
        other_img=[f"/output/{img}" for img in job["other_img"]] if job["other_img"] else None,
        error=job["error"],
    )
    
@app.get("/image/{filename}")
async def get_image(filename: str):
    filepath = f"./output/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath,media_type="image/png")

class CORSStaticFiles(StaticFiles):
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"access-control-allow-origin", b"*"))
                message["headers"] = headers
            await send(message)
        await super().__call__(scope, receive, send_with_cors)


app.mount("/output", StaticFiles(directory="output"), name="output")
