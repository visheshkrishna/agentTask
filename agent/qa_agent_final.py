import subprocess
import sys
import sqlite3
from datetime import datetime
import json
from typing import Optional
import time
import os
import traceback
from playwright.sync_api import sync_playwright
import logging

# Configure database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "qa_tasks.db")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('qa_agent_db')

try:
    from db.database import Database
    db = Database()
    print("Successfully imported Database class")
except ImportError as e:
    print(f"Failed to import Database class: {str(e)}")
    db = None

def log_step(task_id: str, step_message: str):
    try:
        task_id = task_id.strip('"')
        if db is not None:
            try:
                db.log_step(task_id, step_message)
            except Exception as db_error:
                print(f"Database log_step failed: {str(db_error)}")
                _log_step_direct(task_id, step_message)
        else:
            _log_step_direct(task_id, step_message)
    except Exception as e:
        print(f"Error logging step: {str(e)}")
        traceback.print_exc()

def _log_step_direct(task_id: str, step_message: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO logs (task_id, timestamp, message) VALUES (?, ?, ?)",
            (task_id, timestamp, step_message)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging step: {str(e)}")

def _ensure_task_exists(task_id: str, url: str = None, headless: bool = None):
    try:
        conn = sqlite3.connect(DB_PATH)
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                task_id TEXT,
                timestamp TEXT,
                message TEXT
            )
        ''')
        conn.commit()
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE id = ?', (task_id,))
        if cursor.fetchone()[0] == 0:
            print(f"Creating task {task_id} in database (direct)")
            parameters = json.dumps({"url": url, "headless": headless}) if url or headless is not None else None
            cursor.execute(
                'INSERT INTO tasks (id, status, result, logs, parameters) VALUES (?, ?, ?, ?, ?)',
                (task_id, "pending", None, "[]", parameters)
            )
            conn.commit()
    finally:
        if 'conn' in locals():
            conn.close()

def _update_task_direct(task_id: str, status: str, result: Optional[str] = None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        _ensure_task_exists(task_id)
        if result is not None:
            cursor.execute('UPDATE tasks SET status = ?, result = ? WHERE id = ?', (status, result, task_id))
        else:
            cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
        conn.commit()
    finally:
        if 'conn' in locals():
            conn.close()

def run_test_sync(task_id: str, url: str = "https://qacrmdemo.netlify.app", headless: bool = False, goal: str = "add customer"):
    try:
        print(f"Starting test execution for task {task_id} with goal: {goal}")
        task_id = task_id.strip('"')
        log_step(task_id, f"Starting test with direct debug for goal: {goal}")

        if db is not None:
            try:
                task_info = db.get_task(task_id)
                if not task_info:
                    parameters = {"url": url, "headless": headless, "goal": goal}
                    db.create_task(task_id, parameters)
            except Exception as db_error:
                print(f"Database operation failed: {str(db_error)}")
                _ensure_task_exists(task_id, url, headless)
        else:
            _ensure_task_exists(task_id, url, headless)

        log_step(task_id, f"Setting up test with URL: {url}, headless: {headless}")

        script_name = "temp_test.py" if goal.lower() != "verify total customers" else "verify_total_customers.py"
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", script_name)

        log_step(task_id, "Starting test execution")
        os.environ["TEST_URL"] = url
        os.environ["TEST_HEADLESS"] = str(headless)

        python_executable = sys.executable
        log_step(task_id, f"Using Python executable: {python_executable}")
        log_step(task_id, f"Script path: {script_path}")
        if os.path.exists(script_path):
            log_step(task_id, "Script exists")
            log_step(task_id, f"Script size: {os.path.getsize(script_path)} bytes")
        else:
            log_step(task_id, "Script does not exist")
            raise Exception("Failed to locate the script")

        if db is not None:
            try:
                db.update_task(task_id, "running")
            except Exception as db_error:
                print(f"Database update failed: {str(db_error)}")
                _update_task_direct(task_id, "running")
        else:
            _update_task_direct(task_id, "running")

        try:
            env = os.environ.copy()
            env["TEST_URL"] = url
            env["TEST_HEADLESS"] = str(headless)

            process = subprocess.Popen(
                [python_executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )

            for stdout_line in iter(process.stdout.readline, ""):
                if stdout_line:
                    log_step(task_id, stdout_line.strip())
            process.stdout.close()

            stderr = process.stderr.read()
            if stderr:
                log_step(task_id, f"STDERR:\n{stderr}")

            return_code = process.wait()
            log_step(task_id, f"Process completed with return code: {return_code}")

            if return_code == 0:
                _update_task_direct(task_id, "completed", "Test completed successfully")
                return 0
            else:
                result_msg = f"{'Verify total customers test' if goal.lower() == 'verify total customers' else 'Add customer test'} failed with return code {return_code}"
                _update_task_direct(task_id, "failed", result_msg)
                return 1

        except Exception as e:
            error_msg = f"Error running subprocess: {str(e)}"
            log_step(task_id, error_msg)
            traceback.print_exc()
            _update_task_direct(task_id, "failed", error_msg)
            return 1

    except Exception as e:
        error_msg = f"Error during test: {str(e)}"
        traceback.print_exc()
        log_step(task_id, error_msg)
        log_step(task_id, traceback.format_exc())
        if db is not None:
            try:
                db.update_task(task_id, "failed", error_msg)
            except Exception as db_error:
                print(f"Database update failed: {str(db_error)}")
                _update_task_direct(task_id, "failed", error_msg)
        else:
            _update_task_direct(task_id, "failed", error_msg)
        return 1

if __name__ == "__main__":
    run_test_sync("manual-debug-task")
