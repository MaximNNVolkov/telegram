"""Fixed DeepSeek API check with explicit .env path"""
from pathlib import Path
from decouple import Config, RepositoryEnv

env_path = Path("/home/user1/telegram/.env")
if env_path.exists():
    cfg = Config(RepositoryEnv(str(env_path)))
    api_key = cfg("DEEPSEEK_API2")
else:
    api_key = None

from openai import OpenAI
try:
    client = OpenAI(api_key=api_key, base_url='https://api.deepseek.com')
    r = client.chat.completions.create(model='deepseek-chat', messages=[{'role':'user','content':'ping'}], max_tokens=5)
    print('OK:', r.choices[0].message.content)
except Exception as e:
    print('ERROR:', e)
