import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY

def ask_openai(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Bạn là trợ lý AI. Trả về JSON với 'intent' thể hiện hành động: ví dụ go_home, show_profile, logout."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        functions=[
            {
                "name": "navigate",
                "description": "Hành động điều hướng UI",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "intent": {
                            "type": "string",
                            "enum": ["go_home", "show_profile", "logout"]
                        }
                    },
                    "required": ["intent"]
                }
            }
        ],
        function_call={"name": "navigate"}
    )
    return response["choices"][0]["message"]["function_call"]["arguments"]

