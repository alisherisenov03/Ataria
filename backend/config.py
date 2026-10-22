import os

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
DEFAULT_WORKSPACE = os.getenv("DEFAULT_WORKSPACE", "ataria")
BACKEND_TOKEN = os.getenv("BACKEND_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
