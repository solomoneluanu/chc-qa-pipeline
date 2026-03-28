from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch


def load_text_generation_pipeline(model_id: str):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto"
    )

    generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer
    )
    return generator


def generate_summary_with_model(generator, prompt: str, max_new_tokens: int = 500) -> str:
    response = generator(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        temperature=0.1,
        return_full_text=False
    )
    return response[0]["generated_text"].strip()
