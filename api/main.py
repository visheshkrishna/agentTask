"""
FastAPI application for QA Agent.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from typing import Optional, List
import sqlite3
import json
import os
import traceback
import logging
from datetime import datetime
import asyncio
from agent.qa_agent_final import run_test_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("qa_agent_api")

app = FastAPI(
    title="QA Agent API",
    description="API for running automated QA tests on web applications",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Task(BaseModel):
    goal: Optional[str] = None
    headless: bool = False
    url: str = "https://qacrmdemo.netlify.app"

class LogEntry(BaseModel):
    timestamp: str
    message: str

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
    logs: List[LogEntry] = []

def init_db():
    try:
        logger.info("Initializing database")
        conn = sqlite3.connect('qa_tasks.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                status TEXT,
                result TEXT,
                logs TEXT,
                parameters TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialization successful")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        traceback.print_exc()

def update_task_status(task_id: str, status: str, result: Optional[str] = None):
    try:
        conn = sqlite3.connect('qa_tasks.db')
        cursor = conn.cursor()
        if result:
            cursor.execute('UPDATE tasks SET status = ?, result = ? WHERE id = ?', (status, result, task_id))
        else:
            cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating task {task_id} status: {e}")

async def run_test_task(task_id: str, url: str, headless: bool, goal: Optional[str] = None):
    logger.info(f"Starting async task {task_id} for goal '{goal}' at {url}")
    update_task_status(task_id, "running")

    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, run_test_sync, task_id, url, headless)

    if success == 0:
        update_task_status(task_id, "completed", "Tests completed successfully")
    else:
        update_task_status(task_id, "failed", f"Test failed with return code {success}")

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("API server started")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        traceback.print_exc()
        raise

@app.post("/tasks", response_model=TaskResponse)
async def create_task(task: Task):
    task_id = str(uuid.uuid4())
    logger.info(f"Creating task {task_id}")

    task_data = {
        "url": task.url,
        "headless": task.headless,
        "goal": task.goal
    }

    try:
        conn = sqlite3.connect('qa_tasks.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tasks (id, status, result, logs, parameters) VALUES (?, ?, ?, ?, ?)',
            (task_id, "pending", None, "[]", json.dumps(task_data))
        )
        conn.commit()
        conn.close()

        asyncio.create_task(run_test_task(task_id, task.url, task.headless, task.goal))

        return TaskResponse(task_id=task_id, status="pending", result=None, logs=[])
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    try:
        conn = sqlite3.connect('qa_tasks.db')
        cursor = conn.cursor()
        cursor.execute('SELECT status, result, logs FROM tasks WHERE id = ?', (task_id.strip(),))
        result = cursor.fetchone()
        conn.close()

        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")

        status, result_msg, logs = result
        parsed_logs = json.loads(logs) if logs else []

        return TaskResponse(task_id=task_id, status=status, result=result_msg or "", logs=parsed_logs)
    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch task")

@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks():
    try:
        conn = sqlite3.connect('qa_tasks.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, status, result, logs FROM tasks ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()

        task_list = []
        for row in rows:
            task_id, status, result, logs_json = row
            try:
                logs = json.loads(logs_json) if logs_json else []
            except json.JSONDecodeError:
                logs = []
            task_list.append(TaskResponse(task_id=task_id, status=status, result=result or "", logs=logs))

        return task_list
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tasks")

@app.get("/")
async def root():
    return {"message": "QA Agent API is running"}
