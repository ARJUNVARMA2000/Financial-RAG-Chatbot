"""
Model registry for multi-model evaluation.

All models are accessed via OpenRouter using their OpenRouter model identifiers.
"""

from typing import Dict

# Models available for evaluation via OpenRouter
EVAL_MODELS: Dict[str, str] = {
    # Claude models (Anthropic)
    "claude-opus-4.5": "anthropic/claude-opus-4.5",
    "claude-sonnet-4.5": "anthropic/claude-sonnet-4.5",
    # Google models
    "gemini-3-pro": "google/gemini-3-pro-preview",
    # OpenAI models
    "gpt-5.1": "openai/gpt-5.1",
    # Moonshot AI models
    "kimi-k2-thinking": "moonshotai/kimi-k2-thinking",
    # Meta Llama models - best open source
    "llama-4-maverick": "meta-llama/llama-4-maverick",
}

# Judge model for evaluating answer correctness
JUDGE_MODEL = "anthropic/claude-opus-4.5"

# Cost per 1M tokens (approximate, for reference - OpenRouter provides actual costs)
# These are fallback estimates if OpenRouter doesn't return cost info
MODEL_COSTS_PER_1M_TOKENS: Dict[str, Dict[str, float]] = {
    "anthropic/claude-opus-4.5": {"input": 5.0, "output": 25.0},
    "anthropic/claude-sonnet-4.5": {"input": 3.0, "output": 15.0},
    "google/gemini-3-pro-preview": {"input": 2.0, "output": 12.0},
    "openai/gpt-5.1": {"input": 1.25, "output": 10.0},
    "moonshotai/kimi-k2-thinking": {"input": 0.45, "output": 2.35},
    "meta-llama/llama-4-maverick": {"input": 0.136, "output": 0.68},
}


def get_model_id(model_name: str) -> str:
    """Get the OpenRouter model ID for a given model name."""
    if model_name in EVAL_MODELS:
        return EVAL_MODELS[model_name]
    # If it's already a full model ID, return as-is
    if "/" in model_name:
        return model_name
    raise ValueError(f"Unknown model: {model_name}. Available models: {list(EVAL_MODELS.keys())}")


def get_all_model_names() -> list[str]:
    """Get all available model names."""
    return list(EVAL_MODELS.keys())


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for a model based on token counts (fallback if OpenRouter doesn't provide cost)."""
    if model_id in MODEL_COSTS_PER_1M_TOKENS:
        costs = MODEL_COSTS_PER_1M_TOKENS[model_id]
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return input_cost + output_cost
    return 0.0

