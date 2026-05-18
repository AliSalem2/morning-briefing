MODELS = {
    "haiku":    "anthropic/claude-haiku-4-5-20251001",
    "sonnet":   "anthropic/claude-sonnet-4-6",
    "local-small": "ollama/tinyllama",
    "local-mid":   "ollama/phi3:mini",
}

def get_model(name: str = None) -> tuple[str, str | None]:
    """
    Returns (model_string, api_base).
    Call with a name to override, or leave empty to use .env default.
    
    Usage:
        model, base = get_model()          # uses .env
        model, base = get_model("sonnet")  # override to Sonnet
        model, base = get_model("local-small") # override to local
    """
    import os
    from dotenv import load_dotenv
    load_dotenv("config/.env")

    if name:
        model = MODELS.get(name)
        if not model:
            raise ValueError(f"Unknown model '{name}'. Choose from: {list(MODELS.keys())}")
    else:
        model = os.getenv("MODEL_PROVIDER")

    api_base = os.getenv("OLLAMA_API_BASE") if model.startswith("ollama") else None
    return model, api_base
