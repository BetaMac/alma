# backend/agents/manager_agent.py
from typing import List, Dict, Any, Optional, AsyncIterator, AsyncGenerator
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
from transformers import AutoTokenizer
from pathlib import Path

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
    _instance = None
    _model = None
    _model_lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_id: str = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                 model_file: str = "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                 max_retries: int = 3,
                 default_timeout: int = 600,
                 max_memory_percent: float = 0.9):
        """Initialize the Manager Agent with Mistral model."""
        if not hasattr(self, '_initialized'):
            logger.info("Initializing Manager Agent")
            self.model_id = model_id
            self.model_file = model_file
            self.tasks: Dict[str, Task] = {}
            self.active_agents: Dict[str, Any] = {}
            self.max_retries = max_retries
            self.default_timeout = default_timeout
            self.max_memory_percent = max_memory_percent
            self._initialized = True
            if self._model is None:
                self._initialize_model()

    async def get_model(self):
        """Get or initialize the model with thread safety."""
        async with self._model_lock:
            if self._model is None:
                self._initialize_model()
            return self._model

    def _initialize_model(self):
        """Initialize the Mistral model with caching."""
        if self._model is not None:
            return

        try:
            logger.info("Initializing Mistral model...")
            self._check_cuda_memory()
            logger.info(f"Available GPU memory before init: {self._get_available_memory():.2f}MB")
            
            model_path = Path("models") / self.model_file
            
            if not model_path.exists():
                logger.info(f"Downloading model to {model_path}...")
                model_path.parent.mkdir(exist_ok=True)
                from huggingface_hub import hf_hub_download
                hf_hub_download(
                    repo_id=self.model_id,
                    filename=self.model_file,
                    local_dir="models"
                )
            
            self._model = AutoModelForCausalLM.from_pretrained(
                str(model_path),
                model_type="mistral",
                gpu_layers=35,
                context_length=2048,
                max_new_tokens=1024,
                threads=4,
                batch_size=1
            )
            
            logger.info("Model initialized successfully")
            self._verify_model_initialization()
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise ModelInitializationError(f"Model initialization failed: {str(e)}")

    def _verify_model_initialization(self):
        """Verify model initialization with a test generation."""
        try:
            test_output = self._model("Test", max_new_tokens=10)
            if not test_output or len(test_output.strip()) == 0:
                raise ModelInitializationError("Model verification failed: empty output")
            logger.info("Model verification successful")
        except Exception as e:
            raise ModelInitializationError(f"Model verification failed: {str(e)}")

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
                return {
                    "prompt": f"{prompt}",
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
            if self._model:
                del self._model
                self._model = None
            logger.info("Manager Agent cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    async def process_creative_task(self, prompt: str) -> str:
        """Process a creative task with optimized parameters."""
        try:
            await self._ensure_memory_available()
            self._model.reset()
            
            prompt_config = build_creative_prompt(prompt)
            generation_params = {
                **prompt_config['generation_params'],
                'max_new_tokens': 512,
                'temperature': 0.7,
                'top_p': 0.9,
                'repetition_penalty': 1.1,
                'stream': False
            }
            
            response = self._model(prompt_config['prompt'], **generation_params)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error in creative task: {str(e)}")
            raise
        finally:
            self._cleanup_gpu_memory()

    async def process_analytical_task(self, prompt: str) -> AsyncIterator[str]:
        """Process an analytical task with optimized streaming."""
        try:
            await self._ensure_memory_available()
            self._model.reset()
            
            prompt_config = build_analytical_prompt(prompt)
            generation_params = {
                **prompt_config['generation_params'],
                'max_new_tokens': 1024,
                'temperature': 0.3,
                'top_p': 0.85,
                'repetition_penalty': 1.0,
                'stream': True
            }
            
            current_chunk = ""
            chunk_size = 0
            
            for token in self._model(prompt_config['prompt'], **generation_params):
                current_chunk += token
                chunk_size += 1
                
                if chunk_size >= 20 or token[-1] in '.!?\n':
                    yield current_chunk
                    current_chunk = ""
                    chunk_size = 0
                    await asyncio.sleep(0.01)
            
            if current_chunk:
                yield current_chunk
                
        except Exception as e:
            logger.error(f"Error in analytical task: {str(e)}")
            raise
        finally:
            self._cleanup_gpu_memory()

    def _get_available_memory(self) -> float:
        """Get available GPU memory in MB."""
        if not torch.cuda.is_available():
            return 0.0
        
        try:
            torch.cuda.empty_cache()
            return torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
        except Exception as e:
            logger.error(f"Error getting GPU memory: {str(e)}")
            return 0.0

    def _check_cuda_memory(self) -> Dict[str, Any]:
        """Check CUDA memory status."""
        if not torch.cuda.is_available():
            return {
                "available": False,
                "total": 0,
                "reserved": 0,
                "allocated": 0,
                "free": 0,
                "utilization": 0.0
            }
        
        try:
            torch.cuda.empty_cache()
            stats = {
                "available": True,
                "total": torch.cuda.get_device_properties(0).total_memory,
                "reserved": torch.cuda.memory_reserved(0),
                "allocated": torch.cuda.memory_allocated(0),
                "free": torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0),
                "utilization": torch.cuda.memory_allocated(0) / torch.cuda.get_device_properties(0).total_memory * 100
            }
            logger.debug(f"CUDA Memory Stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error checking CUDA memory: {str(e)}")
            return {
                "available": False,
                "error": str(e)
            }

    async def _ensure_memory_available(self) -> None:
        """Ensure sufficient GPU memory is available."""
        if not torch.cuda.is_available():
            return
        
        stats = self._check_cuda_memory()
        if stats["utilization"] > (self.max_memory_percent * 100):
            self._cleanup_gpu_memory()
            stats = self._check_cuda_memory()
            if stats["utilization"] > (self.max_memory_percent * 100):
                raise MemoryError("Insufficient GPU memory available")

    def _cleanup_gpu_memory(self) -> None:
        """Clean up GPU memory."""
        if torch.cuda.is_available():
            try:
                if self._model:
                    self._model.reset()
                
                torch.cuda.empty_cache()
                gc.collect()
                torch.cuda.synchronize()
                
                logger.debug("GPU memory cleanup completed")
                
            except Exception as e:
                logger.error(f"Error during GPU memory cleanup: {str(e)}")

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

    async def process_task(self, prompt: str, task_type: str) -> AsyncGenerator[str, None]:
        """Process a task with streaming response."""
        model = await self.get_model()
        try:
            prompt_config = self._process_prompt(prompt, PromptType(task_type))
            async for chunk in self._generate_response(model, prompt_config):
                yield chunk
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            raise TaskProcessingError(str(e))

    async def _generate_response(self, model, prompt_config: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Generate response with streaming."""
        try:
            response = ""
            chunk_size = 8  # Adjust based on your needs
            
            # Get the full response first
            full_response = model(
                prompt_config['prompt'],
                **prompt_config['generation_params']
            )
            
            # Stream it in chunks
            words = full_response.split()
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                response += chunk + " "
                yield chunk + " "
                await asyncio.sleep(0.1)  # Prevent overwhelming the frontend
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise TaskProcessingError(f"Failed to generate response: {str(e)}")