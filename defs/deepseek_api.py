from decouple import config
from openai import OpenAI


auth_deepseek = config('DEEPSEEK_API2')
client = OpenAI(api_key=auth_deepseek, base_url="https://api.deepseek.com")


# def get_response(user_message: str, sys_message: str = ''):
#     response = client.chat.completions.create(
#         model="deepseek-chat",
#         messages=[
#             {"role": "system", "content": sys_message},
#             {"role": "user", "content": user_message}
#                 ],
#     stream=False
#     )
#     return response

def get_response(user_message: str | None, sys_message: str | None = ''):
    user_content = '' if user_message is None else str(user_message)
    sys_content = '' if sys_message is None else str(sys_message)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_content}
        ],
        stream=False
    )
    return response
