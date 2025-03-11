from decouple import config
from openai import OpenAI


auth_deepseek = config('DEEPSEEK_API2')
client = OpenAI(api_key=auth_deepseek, base_url="https://api.deepseek.com")


def get_response(sys_message, user_message):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": sys_message},
            {"role": "user", "content": user_message}
                ],
    stream=False
    )
    return response
