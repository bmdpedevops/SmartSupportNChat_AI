from groq import Groq
from langchain_community.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from dotenv import load_dotenv
import os

load_dotenv()

OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_AI_BASE = os.getenv("OPENAI_API_BASE")

if OPEN_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is missing. Please set it in your .env file.")
else:
    print(f"OPENAI_API_KEY loaded: {OPEN_API_KEY[:10]}...")

if OPEN_AI_BASE is None:
    raise ValueError("OPENAI_API_BASE is missing. Please set it in your .env file.")
else:
    print(f"OPENAI_API_BASE loaded: {OPEN_AI_BASE}")

os.environ["OPENAI_API_KEY"] = OPEN_API_KEY
os.environ["OPENAI_API_BASE"] = OPEN_AI_BASE
groq_llm = ChatOpenAI(
    model_name="gemma2-9b-it",
    temperature=0.3,
    # max_tokens=32768,  # or lower depending on input size
    streaming=False,
)


from dotenv import load_dotenv
import os

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if ANTHROPIC_API_KEY is None:
    raise ValueError("ANTHROPIC_API_KEY is missing. Please set it in your .env file.")
else:
    print(f"ANTHROPIC_API_KEY loaded: {ANTHROPIC_API_KEY[:10]}...")

os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY

# Use Claude 3 model (e.g., Haiku or Sonnet)
anthropic_llm = ChatAnthropic(
    model="claude-3-haiku-20240307",  # or try sonnet/opus if your account supports
    temperature=0.3,
    streaming=False,
)
