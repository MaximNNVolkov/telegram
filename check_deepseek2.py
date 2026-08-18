from decouple import config
print("DEEPSEEK_API2 found:", bool(config('DEEPSEEK_API2', default=None)))
from openai import OpenAI
try:
    client = OpenAI(api_key=config('DEEPSEEK_API2'), base_url='https://api.deepseek.com')
    r = client.chat.completions.create(model='deepseek-chat', messages=[{'role':'user','content':'ping'}], max_tokens=5)
    print('OK:', r.choices[0].message.content)
except Exception as e:
    print('ERROR:', e)
