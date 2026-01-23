from openai import OpenAI
from google import genai
from openai import AsyncOpenAI

openai_client = OpenAI()
google_client = genai.Client()
async_openai_client = AsyncOpenAI()
