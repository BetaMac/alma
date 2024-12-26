# backend/agents/manager_agent.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ctransformers import AutoModelForCausalLM
from loguru import logger
from enum import Enum
import asyncio
import torch
import gc
import time
import uuid
from contextlib import asynccontextmanager
from .prompt_system import PromptConfig, PromptType, build_creative_prompt, build_analytical_prompt

class ManagerAgentError(Exception):
    """Base exception class for Manager Agent errors"""
    pass

class ModelInitializationError(ManagerAgentError):
    """Raised when the model fails to initialize properly"""
    pass

class TaskValidationError(ManagerAgentError):
    """Raised when a task fails validation checks"""
    pass

class TaskProcessingError(ManagerAgentError):
    """Raised when task processing fails"""
    pass

class TaskTimeoutError(ManagerAgentError):
    """Raised when a task exceeds its timeout period"""
    pass

class InvalidPromptError(ManagerAgentError):
    """Raised when a prompt configuration is invalid"""
    pass

class AgentCommunicationError(ManagerAgentError):
    """Raised when communication between agents fails"""
    pass

class ResourceExhaustedError(ManagerAgentError):
    """Raised when system resources are exhausted"""
    pass

class MemoryError(ManagerAgentError):
    """Raised when memory management fails"""
    pass

class TaskStatus(Enum):
    """Enum for tracking task status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class Task(BaseModel):
    """Model for representing a task in the system"""
    id: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: float  # timestamp
    timeout_seconds: Optional[int] = None
    
    def validate_timeout(self) -> bool:
        """Check if task has exceeded its timeout period"""
        if not self.timeout_seconds:
            return True
        return (time.time() - self.created_at) <= self.timeout_seconds

class ManagerAgent:
    """Core Manager Agent that orchestrates the AI learning system"""
    def _validate_task(self, task: Task) -> None:
        """Validate task parameters before processing."""
        if not task.id:
            raise TaskValidationError("Task ID is required")
        if not task.prompt:
            raise TaskValidationError("Task prompt is required")
        if task.status not in TaskStatus:
            raise TaskValidationError(f"Invalid task status: {task.status}")
            
    def _process_prompt(self, prompt: str, task_type: PromptType) -> Dict[str, Any]:
        """Process and validate prompt based on task type."""
        try:
            if task_type == PromptType.CREATIVE:
                return build_creative_prompt(prompt)
            elif task_type == PromptType.ANALYTICAL:
                return build_analytical_prompt(prompt)
            else:
                # Default to conversational prompt
                return {
                    "prompt": f"[INST] {prompt} [/INST]",
                    "generation_params": {
                        "max_new_tokens": 1024,
                        "temperature": 0.7,
                        "top_p": 0.95
                    }
                }
        except Exception as e:
            logger.error(f"Prompt processing error: {str(e)}")
            raise InvalidPromptError(f"Failed to process prompt: {str(e)}")

    @asynccontextmanager
    async def _task_context(self, task: Task):
        """Context manager for task processing with proper status handling."""
        task.status = TaskStatus.PROCESSING
        try:
            yield
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            raise
        finally:
            if task.status == TaskStatus.PROCESSING:
                task.status = TaskStatus.FAILED
                task.error = "Task processing interrupted"

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """List tasks filtered by status if provided."""
        if status is None:
            return list(self.tasks.values())
        return [task for task in self.tasks.values() if task.status == status]

    async def create_task(self, prompt: str, task_type: PromptType = PromptType.CONVERSATIONAL,
                         timeout_seconds: Optional[int] = None) -> Task:
        """Create and queue a new task."""
        task = Task(
            id=str(uuid.uuid4()),
            prompt=prompt,
            created_at=time.time(),
            timeout_seconds=timeout_seconds,
            metadata={"type": task_type}
        )
        self.tasks[task.id] = task
        return task

    async def cancel_task(self, task_id: str) -> None:
        """Cancel a pending or processing task."""
        if task_id not in self.tasks:
            raise TaskValidationError(f"Task not found: {task_id}")
            
        task = self.tasks[task_id]
        if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            task.status = TaskStatus.CANCELLED
            logger.info(f"Task {task_id} cancelled")
        else:
            logger.warning(f"Cannot cancel task {task_id} in status {task.status}")

    def cleanup(self) -> None:
        """Cleanup resources before shutdown."""
        try:
            self._cleanup_gpu_memory()
            if self.model:
                del self.model
                self.model = None
            logger.info("Manager Agent cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    async def process_creative_task(self, prompt: str) -> str:
        """Process a creative task."""
        task = await self.create_task(prompt, PromptType.CREATIVE)
        processed_task = await self.process_task(task)
        return processed_task.result or ""

    async def process_analytical_task(self, prompt: str) -> str:
        """Process an analytical task."""
        task = await self.create_task(prompt, PromptType.ANALYTICAL)
        processed_task = await self.process_task(task)
        return processed_task.result or ""
    
    def __init__(self, model_id: str = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                 model_file: str = "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                 max_retries: int = 3,
                 default_timeout: int = 600,
                 max_memory_percent: float = 0.9):  # Add memory threshold
        """Initialize the Manager Agent with Mistral model."""
        logger.info("Initializing Manager Agent")
        self.model_id = model_id
        self.model_file = model_file
        self.model = None
        self.tasks: Dict[str, Task] = {}
        self.active_agents: Dict[str, Any] = {}
        self.max_retries = max_retries
        self.default_timeout = default_timeout
        self.max_memory_percent = max_memory_percent
        self._initialize_model()
        
    def _check_cuda_memory(self) -> Dict[str, Any]:
        """Check CUDA memory status and availability"""
        if not torch.cuda.is_available():
            return {"available": False, "error": "CUDA not available"}
            
        try:
            device = torch.cuda.current_device()
            total_memory = torch.cuda.get_device_properties(device).total_memory
            reserved_memory = torch.cuda.memory_reserved(device)
            allocated_memory = torch.cuda.memory_allocated(device)
            free_memory = total_memory - allocated_memory
            
            memory_stats = {
                "available": True,
                "total": total_memory,
                "reserved": reserved_memory,
                "allocated": allocated_memory,
                "free": free_memory,
                "utilization": allocated_memory / total_memory
            }
            
            logger.debug(f"CUDA Memory Stats: {memory_stats}")
            return memory_stats
            
        except Exception as e:
            logger.error(f"Error checking CUDA memory: {str(e)}")
            return {"available": False, "error": str(e)}

    def _cleanup_gpu_memory(self) -> None:
        """Force cleanup of GPU memory"""
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()
                logger.info("GPU memory cleanup performed")
        except Exception as e:
            logger.error(f"Error during GPU memory cleanup: {str(e)}")

    async def _ensure_memory_available(self) -> bool:
        """Check if sufficient memory is available for task processing"""
        memory_stats = self._check_cuda_memory()
        
        if not memory_stats["available"]:
            logger.warning("CUDA not available for memory check")
            return True  # Continue with CPU if CUDA not available
            
        if memory_stats["utilization"] > self.max_memory_percent:
            logger.warning("High GPU memory utilization detected")
            self._cleanup_gpu_memory()
            
            # Recheck after cleanup
            memory_stats = self._check_cuda_memory()
            if memory_stats["utilization"] > self.max_memory_percent:
                raise MemoryError("Insufficient GPU memory available after cleanup")
                
        return True

    def _initialize_model(self) -> None:
        """Initialize the Mistral model with appropriate settings."""
        try:
            logger.info("Initializing Mistral model...")
            
            # Check memory before initialization
            memory_stats = self._check_cuda_memory()
            if memory_stats["available"]:
                logger.info(f"Available GPU memory before init: {memory_stats['free'] / 1024**2:.2f}MB")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                model_file=self.model_file,
                model_type="mistral",
                gpu_layers=50,  # Adjustable based on GPU memory
                context_length=2048  # Adjust based on available memory
            )
            
            # Verify memory after initialization
            if memory_stats["available"]:
                post_init_stats = self._check_cuda_memory()
                logger.info(f"GPU memory used by model: {(memory_stats['free'] - post_init_stats['free']) / 1024**2:.2f}MB")
            
            logger.success("Model initialization successful")
            
        except Exception as e:
            error_msg = f"Failed to initialize model: {str(e)}"
            logger.error(error_msg)
            raise ModelInitializationError(error_msg)

    async def process_task(self, task: Task) -> Task:
        """Process a task with memory management and retries."""
        self._validate_task(task)
        retries = 0
        
        while retries < self.max_retries:
            try:
                async with self._task_context(task):
                    # Check memory availability
                    await self._ensure_memory_available()
                    
                    if not task.validate_timeout():
                        raise asyncio.TimeoutError()
                    
                    task_type = task.metadata.get('type', PromptType.CONVERSATIONAL)
                    prompt_config = self._process_prompt(task.prompt, task_type)
                    
                    # Use asyncio.wait_for for timeout handling
                    timeout = task.timeout_seconds or self.default_timeout
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.model,
                            prompt_config['prompt'],
                            **prompt_config['generation_params']
                        ),
                        timeout=timeout
                    )
                    
                    task.result = response.strip()
                    task.status = TaskStatus.COMPLETED
                    logger.success(f"Task {task.id} completed successfully")
                    
                    # Cleanup after task completion
                    self._cleanup_gpu_memory()
                    break
                    
            except MemoryError as e:
                logger.error(f"Memory error during task {task.id}: {str(e)}")
                await asyncio.sleep(2)  # Wait for memory to potentially free up
                retries += 1
            except (asyncio.TimeoutError, TaskProcessingError) as e:
                retries += 1
                if retries >= self.max_retries:
                    task.status = TaskStatus.FAILED
                    task.error = f"Failed after {retries} attempts: {str(e)}"
                    logger.error(f"Task {task.id} failed permanently: {str(e)}")
                else:
                    logger.warning(f"Retrying task {task.id}, attempt {retries + 1}")
                    await asyncio.sleep(1)  # Brief delay before retry
            finally:
                # Ensure memory cleanup happens even on failure
                self._cleanup_gpu_memory()
            
        return task

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics"""
        return self._check_cuda_memory()

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the manager agent including memory stats"""
        status_counts = {status: len(self.list_tasks(status)) for status in TaskStatus}
        memory_stats = self._check_cuda_memory()
        
        return {
            "active_tasks": len(self.tasks),
            "active_agents": len(self.active_agents),
            "status": "operational",
            "task_statistics": status_counts,
            "model_info": {
                "id": self.model_id,
                "file": self.model_file
            },
            "memory_stats": memory_stats
        }