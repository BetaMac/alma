# backend/agents/prompt_system.py
from typing import Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

class PromptType(Enum):
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    INSTRUCTIONAL = "instructional"
    CONVERSATIONAL = "conversational"

class PromptTemplate(BaseModel):
    type: PromptType
    template: str
    max_tokens: int
    temperature: float
    top_p: float
    top_k: int = 40
    repetition_penalty: float

class PromptConfig:
    """Configuration for different types of prompts with optimized parameters"""
    
    TEMPLATES = {
        PromptType.CREATIVE: PromptTemplate(
            type=PromptType.CREATIVE,
            template="[INST] You are a creative assistant. Be concise and direct. Task: {input} [/INST]",
            max_tokens=512,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
        ),
        PromptType.ANALYTICAL: PromptTemplate(
            type=PromptType.ANALYTICAL,
            template="[INST] You are an analytical assistant. Think step by step and be thorough yet concise. Task: {input} [/INST]",
            max_tokens=1024,
            temperature=0.3,
            top_p=0.85,
            repetition_penalty=1.0,
        ),
        PromptType.CONVERSATIONAL: PromptTemplate(
            type=PromptType.CONVERSATIONAL,
            template="[INST] {input} [/INST]",
            max_tokens=512,
            temperature=0.6,
            top_p=0.9,
            repetition_penalty=1.2,
        )
    }
    
    @classmethod
    def get_template(cls, prompt_type: PromptType) -> PromptTemplate:
        return cls.TEMPLATES[prompt_type]

    @classmethod
    def _optimize_for_length(cls, params: Dict[str, Any], text_length: int) -> Dict[str, Any]:
        """Optimize parameters based on input length."""
        optimized = params.copy()
        
        # For very short inputs (< 50 chars)
        if text_length < 50:
            optimized["max_new_tokens"] = min(256, params["max_new_tokens"])
            optimized["temperature"] *= 1.1
        # For medium inputs (50-200 chars), keep default parameters
        elif text_length < 200:
            pass
        # For long inputs (> 200 chars)
        else:
            optimized["max_new_tokens"] = min(1024, params["max_new_tokens"] * 1.5)
            optimized["temperature"] *= 0.9
        
        return optimized

    @classmethod
    def format_prompt(cls, 
                     prompt_type: PromptType, 
                     **kwargs) -> Dict[str, Any]:
        """Format a prompt with the appropriate template and parameters."""
        template = cls.get_template(prompt_type)
        formatted_prompt = template.template.format(**kwargs)
        
        # Get base parameters
        generation_params = {
            "max_new_tokens": template.max_tokens,
            "temperature": template.temperature,
            "top_p": template.top_p,
            "top_k": template.top_k,
            "repetition_penalty": template.repetition_penalty
        }
        
        # Optimize based on input length if input is provided
        input_length = len(kwargs.get("input", ""))
        optimized_params = cls._optimize_for_length(generation_params, input_length)
        
        return {
            "prompt": formatted_prompt,
            "generation_params": optimized_params
        }

def build_creative_prompt(input_text: str) -> Dict[str, Any]:
    """Build a prompt for creative tasks."""
    return PromptConfig.format_prompt(
        PromptType.CREATIVE,
        input=input_text
    )

def build_analytical_prompt(input_text: str) -> Dict[str, Any]:
    """Build a prompt for analytical tasks."""
    return PromptConfig.format_prompt(
        PromptType.ANALYTICAL,
        input=input_text
    )