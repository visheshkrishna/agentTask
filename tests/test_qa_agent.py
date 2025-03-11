import pytest
from agent.qa_agent_final import run_qa_test_async

@pytest.mark.asyncio
async def test_add_customer():
    """Test adding a new customer to the CRM."""
    task_id = "test_task_123"
    await run_qa_test_async(
        task_id=task_id,
        goal="Add a new customer to the CRM and verify it's saved",
        headless=True  # Run headless for CI/CD
    )

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 