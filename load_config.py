import os
import dotenv

dotenv.load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")
discord_token = os.getenv("DC_TOKEN")