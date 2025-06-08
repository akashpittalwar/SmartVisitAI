# ─── config.py ────────────────────────────────────────────────────────────────
import os
import json
from google import genai
from google.genai import types
from google.cloud import secretmanager

def get_secret(secret_name: str) -> str:
    """
    Fetches the latest version of a secret from Secret Manager.
    Best practice: do not store API keys in plaintext.
    """
    # ── Instead of reading from an env var each time, you can
    #    directly hard-code your project ID here:
    project_id = "Add your project id"  # ← change this to your actual GCP Project ID
    
    # If you ever want to fall back to an environment variable, you could also do:
    # project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    #
    # That way, if you DO set the env var, it uses that, otherwise it defaults below.

    if not project_id:
        raise RuntimeError("Project ID is not set either by code or environment.")

    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Retrieve Gemini API key securely
API_KEY = get_secret("gemini_api_key")
if not API_KEY:
    raise RuntimeError("Failed to fetch GEMINI_API_KEY from Secret Manager")

client = genai.Client(
    api_key=API_KEY,
    http_options={"api_version": "v1alpha"}
)

def pretty_json(raw: str) -> str:
    """Helper to pretty-print JSON (useful for debugging)."""
    try:
        return json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
    except Exception:
        return raw
