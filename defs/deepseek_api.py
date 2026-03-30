from decouple import config
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def _build_client():
    if OpenAI is None:
        raise RuntimeError(
            "Package 'openai' is not installed. Install dependencies from requirements.txt."
        )

    api_key = str(config('DEEPSEEK_API2', default='')).strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API2 is not set.")

    return OpenAI(api_key=api_key, base_url='https://api.deepseek.com')


def get_response(user_message: Optional[str], sys_message: Optional[str] = ''):
    user_content = '' if user_message is None else str(user_message)
    sys_content = '' if sys_message is None else str(sys_message)
    client = _build_client()

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_content}
        ],
        stream=False
    )
    return response
