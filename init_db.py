"""
Initialize the database for QA Agent and set up environment.
"""
import subprocess
import sys
import os
import logging
import traceback
from db.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("init.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("qa_agent_init")

def install_playwright_browsers():
    """Install Playwright browsers."""
    try:
        logger.info("Installing Playwright browsers...")
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("Playwright browsers installed successfully")
            return True
        else:
            logger.error(f"Failed to install Playwright browsers: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error installing Playwright browsers: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Initialize the environment."""
    logger.info("Starting initialization process...")
    
    # Initialize database
    logger.info("Initializing database...")
    db = Database()
    logger.info("Database initialized successfully!")
    
    # Install Playwright browsers
    install_playwright_browsers()
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        logger.info(f"Created logs directory at {logs_dir}")
    
    # Create screenshots directory if it doesn't exist
    screenshots_dir = os.path.join(os.getcwd(), "screenshots")
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
        logger.info(f"Created screenshots directory at {screenshots_dir}")
    
    logger.info("Initialization complete!")

if __name__ == "__main__":
    main() 