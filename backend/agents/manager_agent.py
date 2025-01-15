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
import psutil
import subprocess
import json
from .memory_manager import MemoryManager

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
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    task_type: Optional[str] = None
    execution_time: Optional[float] = None
    
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
            self.recent_tasks: List[Task] = []  # Keep track of recent tasks
            self.max_recent_tasks = 10  # Maximum number of recent tasks to store
            self.memory_manager = MemoryManager()  # Initialize memory manager

    async def get_model(self):
        """Get or initialize the model with thread safety."""
        # Don't automatically initialize
        return self._model

    def _initialize_model(self):
        """Initialize the Mistral model with caching."""
        if self._model is not None:
            return

        try:
            logger.info("Initializing Mistral model...")
            logger.info("GPU Memory before model load:")
            memory_before = self._check_cuda_memory()
            logger.info(f"  Used: {memory_before['allocated']/1024/1024:.2f}MB")
            logger.info(f"  Free: {memory_before['free']/1024/1024:.2f}MB")
            logger.info(f"  Utilization: {memory_before['utilization']:.2f}%")
            
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
                context_length=4096,
                max_new_tokens=2048,
                threads=4,
                batch_size=1
            )
            
            # Track memory after model load
            logger.info("GPU Memory after model load:")
            memory_after = self._check_cuda_memory()
            logger.info(f"  Used: {memory_after['allocated']/1024/1024:.2f}MB")
            logger.info(f"  Free: {memory_after['free']/1024/1024:.2f}MB")
            logger.info(f"  Utilization: {memory_after['utilization']:.2f}%")
            logger.info(f"Memory used by model: {(memory_after['allocated'] - memory_before['allocated']) / 1024 / 1024:.2f}MB")
            
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

    async def _process_prompt(self, prompt: str, task_type: PromptType, task_id: str) -> Dict[str, Any]:
        """Process and validate prompt based on task type."""
        try:
            # Get relevant context from memory
            context_items = await self.memory_manager.get_relevant_context(prompt)
            context_summary = await self.memory_manager.summarize_context(context_items)
            
            # Build prompt with context
            if context_summary:
                enhanced_prompt = f"{context_summary}\n\nCurrent request:\n{prompt}"
            else:
                enhanced_prompt = prompt
            
            if task_type == PromptType.CREATIVE:
                return build_creative_prompt(enhanced_prompt)
            elif task_type == PromptType.ANALYTICAL:
                return build_analytical_prompt(enhanced_prompt)
            else:
                return {
                    "prompt": enhanced_prompt,
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
            logger.info("GPU Memory before cleanup:")
            memory_before = self._check_cuda_memory()
            logger.info(f"  Used: {memory_before['allocated']/1024/1024:.2f}MB")
            logger.info(f"  Utilization: {memory_before['utilization']:.2f}%")

            if self._model:
                del self._model
                self._model = None

            logger.info("GPU Memory after cleanup:")
            memory_after = self._check_cuda_memory()
            logger.info(f"  Used: {memory_after['allocated']/1024/1024:.2f}MB")
            logger.info(f"  Utilization: {memory_after['utilization']:.2f}%")
            logger.info(f"Memory freed: {(memory_before['allocated'] - memory_after['allocated']) / 1024 / 1024:.2f}MB")

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

    async def process_analytical_task(self, task: Task) -> AsyncGenerator[str, None]:
        """Process an analytical task with streaming support."""
        generation_params = {
            'max_new_tokens': 4096,  # Increased from 2048
            'temperature': 0.3,
            'top_p': 0.85,
            'stream': True
        }
        
        current_chunk = ""
        total_tokens = 0
        
        async for token in self._generate_response(task.prompt, generation_params):
            current_chunk += token
            total_tokens += 1
            
            # Yield on natural breaks or when chunk is large enough
            if (len(current_chunk) >= 8 or 
                any(p in current_chunk for p in ['.', '!', '?', '\n'])):
                yield current_chunk
                current_chunk = ""
            
            # Safety check for token limit
            if total_tokens >= 4096:
                logger.warning(f"Reached token limit of 4096 at position {total_tokens}")
                if current_chunk:
                    yield current_chunk
                break

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

    @staticmethod
    def _get_gpu_memory():
        """Get GPU memory info using nvidia-smi."""
        try:
            result = subprocess.check_output(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total,memory.free', '--format=csv,nounits,noheader'],
                encoding='utf-8'
            )
            used, total, free = map(int, result.strip().split(','))
            return {
                "available": True,
                "total": total * 1024 * 1024,  # Convert MB to bytes
                "allocated": used * 1024 * 1024,
                "free": free * 1024 * 1024,
                "utilization": (used / total) * 100,
                "peak": used * 1024 * 1024  # Current usage as peak
            }
        except Exception as e:
            logger.error(f"Error getting GPU memory: {str(e)}")
            return {
                "available": False,
                "total": 0,
                "allocated": 0,
                "free": 0,
                "utilization": 0,
                "peak": 0
            }

    def _check_cuda_memory(self) -> Dict[str, Any]:
        """Check system and GPU memory status."""
        try:
            # Get GPU memory info
            gpu_stats = self._get_gpu_memory()
            
            # Get system memory info
            system_memory = psutil.virtual_memory()
            
            stats = {
                **gpu_stats,
                "system_total": system_memory.total,
                "system_used": system_memory.used,
                "system_free": system_memory.free,
                "system_percent": system_memory.percent
            }
            
            logger.debug(f"Memory Stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error checking memory: {str(e)}")
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
        try:
            if self._model:
                # Instead of using reset(), we'll recreate the model if needed
                self._model = None
                torch.cuda.empty_cache()
            
            # Record memory stats
            stats = self._check_cuda_memory()
            logger.debug(f"Memory after cleanup: GPU Used={stats['allocated']/1024/1024:.2f}MB, System Used={stats['system_used']/1024/1024/1024:.2f}GB")
            
        except Exception as e:
            logger.error(f"Error during memory cleanup: {str(e)}")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics"""
        return self._check_cuda_memory()

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the manager agent including memory stats"""
        status_counts = {status: len(self.list_tasks(status)) for status in TaskStatus}
        memory_stats = self._check_cuda_memory()
        
        # Format recent tasks for the UI
        recent_tasks_info = [
            {
                "id": task.id,
                "type": task.task_type,
                "status": task.status.value,
                "input_tokens": task.input_tokens,
                "output_tokens": task.output_tokens,
                "execution_time": task.execution_time,
                "created_at": task.created_at,
                "prompt": task.prompt[:100] + "..." if task.prompt else None
            }
            for task in self.recent_tasks
        ]
        
        return {
            "active_tasks": len(self.tasks),
            "active_agents": len(self.active_agents),
            "status": "operational",
            "task_statistics": status_counts,
            "model_info": {
                "id": self.model_id,
                "file": self.model_file,
                "loaded": self._model is not None
            },
            "memory_stats": memory_stats,
            "recent_tasks": recent_tasks_info
        }

    async def process_task(self, prompt: str, task_type: str) -> AsyncGenerator[str, None]:
        """Process a task with streaming response and detailed memory tracking."""
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        # Create task with accurate token count
        input_tokens = self._count_tokens(prompt)
        task = Task(
            id=task_id,
            prompt=prompt,
            status=TaskStatus.PROCESSING,
            created_at=start_time,
            task_type=task_type,
            input_tokens=input_tokens
        )
        
        # Calculate max tokens based on input length
        max_new_tokens = min(4096, max(512, input_tokens * 2))  # Dynamic token limit
        
        self.tasks[task_id] = task
        model = await self.get_model()
        
        try:
            # Track memory before processing
            logger.info("GPU Memory before task:")
            memory_before = self._check_cuda_memory()
            logger.info(f"  Used: {memory_before['allocated']/1024/1024:.2f}MB")
            logger.info(f"  Free: {memory_before['free']/1024/1024:.2f}MB")
            logger.info(f"  Utilization: {memory_before['utilization']:.2f}%")
            
            # Process the prompt with dynamic token limit
            prompt_config = {
                "prompt": f"[INST] {prompt} [/INST]",
                "generation_params": {
                    "max_new_tokens": max_new_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "repetition_penalty": 1.1,
                    "stream": True
                }
            }
            
            response_text = ""
            output_tokens = 0
            
            # Process task with streaming and token counting
            async for chunk in self._generate_response(model, prompt_config):
                response_text += chunk
                output_tokens += self._count_tokens(chunk)
                yield chunk
            
            # Update task with completion info
            execution_time = time.time() - start_time
            task.status = TaskStatus.COMPLETED
            task.result = response_text
            task.output_tokens = output_tokens  # Use accurate token count
            task.execution_time = execution_time
            
            # Add to recent tasks with memory info
            memory_after = self._check_cuda_memory()
            task.metadata.update({
                "peak_memory": memory_after['peak']/1024/1024,
                "memory_used": (memory_after['allocated'] - memory_before['allocated'])/1024/1024,
                "tokens_per_second": output_tokens / execution_time if execution_time > 0 else 0
            })
            
            # Update recent tasks list
            self.recent_tasks.insert(0, task)
            self.recent_tasks = self.recent_tasks[:self.max_recent_tasks]
            
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            raise TaskProcessingError(str(e))
        finally:
            # Cleanup after task completion
            self._cleanup_gpu_memory()

    async def _generate_response(self, model, prompt_config: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Generate response with streaming and adaptive buffering."""
        try:
            current_chunk = ""
            chunk_size = 0
            total_tokens = 0
            last_yield_time = time.time()
            
            # Adaptive buffer settings
            min_buffer_size = 8
            max_buffer_size = 32
            current_buffer_size = min_buffer_size
            min_chunk_interval = 0.05  # Minimum time between chunks in seconds
            
            # Token processing settings
            natural_breaks = {'.', '!', '?', '\n', ',', ';', ':'}
            strong_breaks = {'.', '!', '?', '\n'}
            
            for token in model(prompt_config['prompt'], **prompt_config['generation_params']):
                current_chunk += token
                chunk_size += 1
                total_tokens += 1
                
                current_time = time.time()
                time_since_last_yield = current_time - last_yield_time
                
                # Determine if we should yield based on multiple factors
                should_yield = False
                
                # Check for natural breaks
                if any(p in token for p in strong_breaks):
                    should_yield = True
                elif chunk_size >= current_buffer_size:
                    should_yield = True
                elif time_since_last_yield >= min_chunk_interval and any(p in token for p in natural_breaks):
                    should_yield = True
                
                if should_yield:
                    yield current_chunk
                    
                    # Adapt buffer size based on token generation speed
                    tokens_per_second = chunk_size / time_since_last_yield if time_since_last_yield > 0 else 0
                    if tokens_per_second > 50:  # Fast generation
                        current_buffer_size = min(current_buffer_size + 2, max_buffer_size)
                    elif tokens_per_second < 20:  # Slow generation
                        current_buffer_size = max(current_buffer_size - 1, min_buffer_size)
                    
                    # Reset chunk tracking
                    current_chunk = ""
                    chunk_size = 0
                    last_yield_time = current_time
                    
                    # Adaptive delay based on buffer size
                    delay = max(0.01, min(0.05, 1 / tokens_per_second if tokens_per_second > 0 else 0.05))
                    await asyncio.sleep(delay)
            
            # Yield any remaining tokens
            if current_chunk:
                yield current_chunk
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise TaskProcessingError(f"Failed to generate response: {str(e)}")

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using the model's tokenizer."""
        try:
            # Use cached tokenizer if available
            if hasattr(self, '_tokenizer'):
                return len(self._tokenizer.encode(text))
            
            # Initialize tokenizer if not available
            if not hasattr(self, '_tokenizer'):
                from transformers import AutoTokenizer
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.model_id,
                    use_fast=True,
                    local_files_only=True
                )
            return len(self._tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Error in token counting: {str(e)}, falling back to word count")
            return len(text.split())  # Fallback to word count

    def unload_model(self) -> None:
        """Unload the model from GPU to free up memory."""
        try:
            if self._model:
                # Delete the model to free GPU memory
                del self._model
                self._model = None
                
                # Clear GPU cache
                torch.cuda.empty_cache()
                
                logger.info("Model successfully unloaded from GPU.")
                
                # Log memory stats after unloading
                stats = self._check_cuda_memory()
                logger.debug(f"Memory after unloading: GPU Used={stats['allocated']/1024/1024:.2f}MB, System Used={stats['system_used']/1024/1024/1024:.2f}GB")
        except Exception as e:
            logger.error(f"Error unloading model: {str(e)}")