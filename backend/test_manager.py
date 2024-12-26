# backend/test_manager.py
from agents.manager_agent import ManagerAgent
from loguru import logger
import asyncio

async def test_basic_functionality():
    """Test basic functionality of the ManagerAgent."""
    logger.info("Starting basic functionality test...")
    
    # Initialize agent
    agent = ManagerAgent()
    
    # Test 1: Create and process a simple task
    logger.info("\n=== Test 1: Simple task processing ===")
    task = agent.add_task("Write a short poem about artificial intelligence.")
    result = await agent.process_task(task)
    logger.info("\nAI Response:")
    logger.info("-" * 50)
    logger.info(f"{result.result}")
    logger.info("-" * 50)
    
    # Test 2: Check task status tracking
    logger.info("\n=== Test 2: Task status tracking ===")
    task_status = agent.get_task_status(task.id)
    logger.info(f"Task status: {task_status.status}")
    
    # Test 3: List all tasks
    logger.info("\n=== Test 3: Task listing ===")
    all_tasks = agent.list_tasks()
    logger.info(f"Number of tasks: {len(all_tasks)}")
    
    # Test 4: Check agent status
    logger.info("\n=== Test 4: Agent status ===")
    status = agent.get_status()
    logger.info(f"Agent status: {status}")
    
    logger.success("\nAll tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())