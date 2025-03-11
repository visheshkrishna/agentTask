"""
Database operations for QA Agent tasks.
"""
import sqlite3
from datetime import datetime
import json
import traceback
import logging
from typing import Optional, Dict, List, Any

# Configure logging
logger = logging.getLogger("qa_agent_db")

class Database:
    def __init__(self, db_path: str = 'qa_tasks.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        conn = None
        try:
            logger.info(f"Initializing database at {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tasks table with updated schema
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                result TEXT,
                logs TEXT DEFAULT '[]',
                parameters TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Add columns if they don't exist
            columns_to_add = {
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "parameters": "TEXT",
                "result": "TEXT", 
                "logs": "TEXT DEFAULT '[]'"
            }
            
            for column, type_def in columns_to_add.items():
                try:
                    cursor.execute(f'ALTER TABLE tasks ADD COLUMN {column} {type_def}')
                    logger.info(f"Added column {column} to tasks table")
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
            
            conn.commit()
            logger.info("Database initialization complete")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            traceback.print_exc()
        finally:
            if conn:
                conn.close()

    def create_task(self, task_id: str, parameters: dict = None) -> None:
        """Create a new task."""
        conn = None
        try:
            logger.info(f"Creating task {task_id}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Check if task already exists
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE id = ?', (task_id,))
            if cursor.fetchone()[0] > 0:
                logger.warning(f"Task {task_id} already exists, updating instead")
                cursor.execute(
                    'UPDATE tasks SET status = ?, updated_at = ?, parameters = ? WHERE id = ?',
                    ("pending", now, json.dumps(parameters) if parameters else None, task_id)
                )
            else:
                cursor.execute(
                    'INSERT INTO tasks (id, status, result, logs, parameters, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (task_id, "pending", "", "[]", json.dumps(parameters) if parameters else None, now, now)
                )
            
            conn.commit()
            logger.info(f"Task {task_id} created successfully")
        except Exception as e:
            logger.error(f"Error creating task {task_id}: {str(e)}")
            traceback.print_exc()
        finally:
            if conn:
                conn.close()

    def update_task(self, task_id: str, status: str, result: Optional[str] = None) -> None:
        """Update task status and result."""
        conn = None
        try:
            logger.info(f"Updating task {task_id} with status {status}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Check if task exists
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE id = ?', (task_id,))
            if cursor.fetchone()[0] == 0:
                logger.warning(f"Task {task_id} not found, creating new task")
                self.create_task(task_id)
                
            if result:
                cursor.execute(
                    'UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?',
                    (status, result, now, task_id)
                )
            else:
                cursor.execute(
                    'UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?',
                    (status, now, task_id)
                )
            
            conn.commit()
            logger.info(f"Task {task_id} updated successfully")
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {str(e)}")
            traceback.print_exc()
        finally:
            if conn:
                conn.close()

    def log_step(self, task_id: str, message: str) -> None:
        """Add a log message to task."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing logs
            cursor.execute('SELECT logs FROM tasks WHERE id = ?', (task_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Task {task_id} not found, creating new task")
                self.create_task(task_id)
                
                # Try again to get logs
                cursor.execute('SELECT logs FROM tasks WHERE id = ?', (task_id,))
                result = cursor.fetchone()
                
            existing_logs = json.loads(result[0]) if result and result[0] else []
            
            # Add new log
            new_log = {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "message": message
            }
            existing_logs.append(new_log)
            
            # Update logs and updated_at
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                'UPDATE tasks SET logs = ?, updated_at = ? WHERE id = ?',
                (json.dumps(existing_logs), now, task_id)
            )
            
            conn.commit()
            # Only log info for significant events to avoid excessive logging
            if "error" in message.lower() or "fail" in message.lower() or "success" in message.lower():
                logger.info(f"Task {task_id} log: {message}")
        except Exception as e:
            logger.error(f"Error logging to task {task_id}: {str(e)}")
            traceback.print_exc()
        finally:
            if conn:
                conn.close()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task details."""
        conn = None
        try:
            logger.info(f"Getting task {task_id}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT status, result, logs, parameters, created_at, updated_at FROM tasks WHERE id = ?',
                (task_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Task {task_id} not found")
                return None
                
            status, result_text, logs, parameters, created_at, updated_at = result
            
            # Parse JSON fields
            try:
                parsed_logs = json.loads(logs) if logs else []
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing logs for task {task_id}: {str(e)}")
                parsed_logs = []
                
            try:
                parsed_parameters = json.loads(parameters) if parameters else {}
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing parameters for task {task_id}: {str(e)}")
                parsed_parameters = {}
                
            return {
                "id": task_id,
                "status": status,
                "result": result_text,
                "logs": parsed_logs,
                "parameters": parsed_parameters,
                "created_at": created_at,
                "updated_at": updated_at
            }
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {str(e)}")
            traceback.print_exc()
            return None
        finally:
            if conn:
                conn.close()

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks."""
        conn = None
        try:
            logger.info("Getting all tasks")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT id, status, result, logs, parameters, created_at, updated_at FROM tasks ORDER BY created_at DESC'
            )
            results = cursor.fetchall()
            
            tasks = []
            for task_id, status, result, logs, parameters, created_at, updated_at in results:
                try:
                    parsed_logs = json.loads(logs) if logs else []
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing logs for task {task_id}: {str(e)}")
                    parsed_logs = []
                    
                try:
                    parsed_parameters = json.loads(parameters) if parameters else {}
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing parameters for task {task_id}: {str(e)}")
                    parsed_parameters = {}
                
                tasks.append({
                    "id": task_id,
                    "status": status,
                    "result": result,
                    "logs": parsed_logs,
                    "parameters": parsed_parameters,
                    "created_at": created_at,
                    "updated_at": updated_at
                })
            
            logger.info(f"Retrieved {len(tasks)} tasks")
            return tasks
        except Exception as e:
            logger.error(f"Error getting all tasks: {str(e)}")
            traceback.print_exc()
            return []
        finally:
            if conn:
                conn.close() 