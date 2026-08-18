from decouple import config
from openai import OpenAI
try:
    client = OpenAI(api_key=config('DEEPSEEK_API2'), base_url='https://api.deepseek.com')
    r = client.chat.completions.create(model='deepseek-chat', messages=[{'role':'user','content':'ping'}], max_tokens=5)
    print('DEEPSEEK: OK - ' + r.choices[0].message.content)
except Exception as e:
    print('DEEPSEEK: ERROR - ' + str(e))
