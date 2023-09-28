import os

import dotenv
import openai

dotenv.load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]
