import json
import time
from typing import Optional

from decouple import config

import logger

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


log = logger.get_logger(__name__)

_RETRY_DELAYS = [1, 3, 10, 30]  # секунды между попытками


def _build_client():
    if OpenAI is None:
        raise RuntimeError(
            "Package 'openai' is not installed. Install dependencies from requirements.txt."
        )

    api_key = str(config('DEEPSEEK_API2', default='')).strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API2 is not set.")

    return OpenAI(api_key=api_key, base_url='https://api.deepseek.com')


def _serialize_response(response) -> str:
    if response is None:
        return 'null'

    if hasattr(response, 'model_dump_json'):
        try:
            return response.model_dump_json(indent=2, exclude_none=False)
        except TypeError:
            return response.model_dump_json(indent=2)

    if hasattr(response, 'model_dump'):
        return json.dumps(
            response.model_dump(),
            ensure_ascii=False,
            indent=2,
            default=str
        )

    if hasattr(response, 'to_dict'):
        return json.dumps(
            response.to_dict(),
            ensure_ascii=False,
            indent=2,
            default=str
        )

    return str(response)


def get_response(user_message: Optional[str], sys_message: Optional[str] = ''):
    user_content = '' if user_message is None else str(user_message)
    sys_content = '' if sys_message is None else str(sys_message)
    client = _build_client()

    last_error = None
    for attempt, delay in enumerate(_RETRY_DELAYS + [0]):  # 4 retries + final try
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": sys_content},
                    {"role": "user", "content": user_content}
                ],
                stream=False,
                timeout=30,
            )
            log.info('DeepSeek API response:\n%s', _serialize_response(response))
            return response
        except Exception as e:
            last_error = e
            if attempt < len(_RETRY_DELAYS):
                log.warning(
                    'DeepSeek API error (attempt %d/%d): %s — retry in %ds',
                    attempt + 1, len(_RETRY_DELAYS) + 1, e, delay,
                )
                time.sleep(delay)
            else:
                log.exception('DeepSeek API failed after all retries')

    raise last_error  # type: ignore[misc]
