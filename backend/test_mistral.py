# test_mistral.py
from transformers import AutoTokenizer
from ctransformers import AutoModelForCausalLM
from loguru import logger

def setup_mistral():
    logger.info("Starting Mistral 7B setup...")
    
    # Using GGUF version which is more memory efficient
    model_id = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
    model_file = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"  # Q4 quantization for efficiency
    
    logger.info("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        model_file=model_file,
        model_type="mistral",
        gpu_layers=50  # Adjust based on your GPU memory
    )
    
    logger.info("Testing model with a simple prompt...")
    prompt = "Write a short sentence about AI:"
    
    response = model(prompt, max_new_tokens=50, temperature=0.7)
    logger.info(f"Test response: {response}")
    
    return model

if __name__ == "__main__":
    try:
        # First ensure we have ctransformers with CUDA
        import torch
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        logger.info(f"GPU Device: {torch.cuda.get_device_name(0)}")
        
        model = setup_mistral()
        logger.success("Mistral 7B setup completed successfully!")
    except Exception as e:
        logger.error(f"Error during setup: {str(e)}")