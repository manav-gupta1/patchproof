import os
from packages.ai.provider_factory import create_model_client

provider = os.environ.get("PATCHPROOF_MODEL_PROVIDER", "openai")
print(f"provider={provider}")
print("configured=", bool(
    os.environ.get("OPENAI_API_KEY") if provider == "openai"
    else os.environ.get("ANTHROPIC_API_KEY")
))
