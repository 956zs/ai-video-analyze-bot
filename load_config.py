import os
import dotenv

dotenv.load_dotenv()

discord_token = os.getenv("DC_TOKEN")
if not discord_token:
    raise ValueError("Missing required environment variable: DC_TOKEN")

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Missing required environment variable: OPENAI_API_KEY")

openai_base_url = os.getenv("OPENAI_BASE_URL")