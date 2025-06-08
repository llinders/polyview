from dotenv import load_dotenv
import os

load_dotenv()

print("✅ .env loaded in conftest.py")
print(f"DEBUG: ENV VAR = {os.getenv('TAVILY_API_KEY')}")