# backend/test_prompt_system.py
from agents.manager_agent import ManagerAgent
from agents.prompt_system import PromptType
from loguru import logger
import asyncio
import time

async def test_prompt_system():
    """Test the prompt system with different types of prompts."""
    logger.info("Starting prompt system test...")
    
    agent = ManagerAgent()
    
    # Test creative prompt
    logger.info("\n=== Testing Creative Prompt ===")
    start_time = time.time()
    creative_task = agent.add_task(
        "Write a haiku about technology",
        metadata={"type": PromptType.CREATIVE}
    )
    result = await agent.process_task(creative_task)
    logger.info(f"Time taken: {time.time() - start_time:.2f} seconds")
    logger.info("\nCreative Response:")
    logger.info("-" * 50)
    logger.info(f"{result.result}")
    logger.info("-" * 50)
    
    # Test analytical prompt
    logger.info("\n=== Testing Analytical Prompt ===")
    start_time = time.time()
    analytical_task = agent.add_task(
        "What are the key components of a successful AI system?",
        metadata={"type": PromptType.ANALYTICAL}
    )
    result = await agent.process_task(analytical_task)
    logger.info(f"Time taken: {time.time() - start_time:.2f} seconds")
    logger.info("\nAnalytical Response:")
    logger.info("-" * 50)
    logger.info(f"{result.result}")
    logger.info("-" * 50)
    
    logger.success("All prompt tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_prompt_system())