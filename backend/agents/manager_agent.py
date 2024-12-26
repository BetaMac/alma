"""Updated manager_agent.py with streaming support"""

# [Previous imports remain the same...]

class ManagerAgent:
    # [Previous methods remain the same until process_analytical_task]

    async def process_analytical_task(self, prompt: str):
        """Process an analytical task with streaming support."""
        task = await self.create_task(prompt, PromptType.ANALYTICAL)
        self._validate_task(task)
        
        try:
            await self._ensure_memory_available()
            
            if not task.validate_timeout():
                raise asyncio.TimeoutError()
            
            # Process prompt
            prompt_config = self._process_prompt(task.prompt, PromptType.ANALYTICAL)
            
            # Initialize the model for streaming
            self.model.reset()
            tokens = []
            current_chunk = ""
            
            async def process_stream():
                nonlocal current_chunk
                # Stream response token by token
                for token in self.model(
                    prompt_config['prompt'],
                    stream=True,
                    **prompt_config['generation_params']
                ):
                    tokens.append(token)
                    current_chunk += token
                    
                    # Yield when we have a meaningful chunk (word or punctuation)
                    if token.strip() and (token[-1] in ' .,!?;:' or len(current_chunk) > 20):
                        yield current_chunk
                        current_chunk = ""
                
                # Yield any remaining content
                if current_chunk:
                    yield current_chunk
            
            # Use asyncio.wait_for for timeout handling
            timeout = task.timeout_seconds or self.default_timeout
            try:
                async for chunk in asyncio.wait_for(process_stream(), timeout=timeout):
                    yield chunk
                    
                task.status = TaskStatus.COMPLETED
                task.result = "".join(tokens)
                logger.success(f"Task {task.id} completed successfully")
                
            except asyncio.TimeoutError:
                task.status = TaskStatus.TIMEOUT
                task.error = "Task exceeded timeout limit"
                raise TaskTimeoutError(f"Task {task.id} exceeded timeout of {timeout}s")
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Error processing analytical task {task.id}: {str(e)}")
            raise
            
        finally:
            # Cleanup after task completion
            self._cleanup_gpu_memory()