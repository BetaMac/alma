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
            template="[INST] Create {format} about {subject}. Focus on {aspect}. {additional_context} [/INST]",
            max_tokens=256,
            temperature=0.7,
            top_p=0.95,
            repetition_penalty=1.1,
        ),
        PromptType.ANALYTICAL: PromptTemplate(
            type=PromptType.ANALYTICAL,
            template="[INST] Analyze {subject} in terms of {aspect}. Consider {factors}. {additional_context} [/INST]",
            max_tokens=512,
            temperature=0.3,
            top_p=0.85,
            repetition_penalty=1.0,
        ),
        PromptType.INSTRUCTIONAL: PromptTemplate(
            type=PromptType.INSTRUCTIONAL,
            template="[INST] Explain how to {action} regarding {subject}. Include {details}. {additional_context} [/INST]",
            max_tokens=384,
            temperature=0.4,
            top_p=0.9,
            repetition_penalty=1.0,
        ),
        PromptType.CONVERSATIONAL: PromptTemplate(
            type=PromptType.CONVERSATIONAL,
            template="[INST] {context} {query} [/INST]",
            max_tokens=128,
            temperature=0.6,
            top_p=0.9,
            repetition_penalty=1.2,
        )
    }
    
    @classmethod
    def get_template(cls, prompt_type: PromptType) -> PromptTemplate:
        return cls.TEMPLATES[prompt_type]

    @classmethod
    def format_prompt(cls, 
                     prompt_type: PromptType, 
                     **kwargs) -> Dict[str, Any]:
        """Format a prompt with the appropriate template and parameters."""
        template = cls.get_template(prompt_type)
        formatted_prompt = template.template.format(**kwargs)
        
        return {
            "prompt": formatted_prompt,
            "generation_params": {
                "max_new_tokens": template.max_tokens,
                "temperature": template.temperature,
                "top_p": template.top_p,
                "top_k": template.top_k,
                "repetition_penalty": template.repetition_penalty
            }
        }

# Example prompt builders for specific use cases
def build_creative_prompt(format: str, subject: str, aspect: str, 
                         additional_context: str = "") -> Dict[str, Any]:
    """Build a prompt for creative tasks like poetry or stories."""
    return PromptConfig.format_prompt(
        PromptType.CREATIVE,
        format=format,
        subject=subject,
        aspect=aspect,
        additional_context=additional_context
    )

def build_analytical_prompt(subject: str, aspect: str, factors: str,
                          additional_context: str = "") -> Dict[str, Any]:
    """Build a prompt for analytical tasks."""
    return PromptConfig.format_prompt(
        PromptType.ANALYTICAL,
        subject=subject,
        aspect=aspect,
        factors=factors,
        additional_context=additional_context
    )