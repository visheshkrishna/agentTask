
# QA Agent with API Integration

This project implements an automated QA testing solution with API integration for testing web applications. It specifically focuses on testing the QA CRM Demo Site (https://qacrmdemo.netlify.app/).

## Features

- Automated testing of customer form functionality
- Automated testing of report creation and persistence
- REST API for triggering tests and retrieving results
- Detailed test logging and bug reporting
- Background task processing
- SQLite database for task persistence

## Project Structure

```
.
├── api/
│   ├── __init__.py
│   └── main.py           # FastAPI application
├── agent/
│   ├── __init__.py
│   └── qa_agent.py       # QA testing logic
├── db/
│   ├── __init__.py
│   └── database.py       # Database operations
├── tests/               # Test files
├── requirements.txt     # Project dependencies
├── init_db.py          # Database initialization
└── README.md           # This file
```

## Setup

1. Clone the repository

```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository
```

2. Create and activate a virtual environment:
For Windows users:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows, use this to activate the virtual environment
```
For macOS/Linux users:
```bash
python3 -m venv venv
source venv/bin/activate  # This activates the virtual environment
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install  # Install browser binaries
```

4. Initialize the database:
```bash
python init_db.py
```

## Running the Application

1. Start the API server:
```bash
uvicorn api.main:app --reload
```

2. The API will be available at http://localhost:8000

## API Endpoints

### Create a Test Task
```http
POST /tasks
Content-Type: application/json

{
    "goal": "Test customer form and report creation",
    "headless": true,
    "url": "https://qacrmdemo.netlify.app"
}
```

### Get Task Status
```http
GET /tasks/{task_id}
```

## Example Usage

1. Create a new test task:
```bash
curl -X POST "http://localhost:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{"goal": "Test customer form and report creation", "headless": true}'
```

2. Check task status:
```bash
curl "http://localhost:8000/tasks/{task_id}"
```

## Features Tested

1. Customer Form:
   - Form field input functionality
   - Form submission
   - Validation of required fields
   - Success verification

2. Report Creation:
   - Report form functionality
   - Data source selection
   - Date range selection
   - Report persistence
   - Report details page
   - Report list verification

## Known Issues and Future Improvements

1. Current Limitations:
   - Form field interaction can be flaky
   - Report persistence verification needs improvement
   - Limited error recovery

2. Future Improvements:
   - Add retry mechanisms for flaky operations
   - Implement better error handling
   - Add more comprehensive test scenarios
   - Implement test result caching
   - Add API authentication
   - Add parallel test execution support

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 
=======
# agentTask
>>>>>>> 0a113e1d21450f447f7b61fbe23f94d25e86978c
