from openai import OpenAI

try:
    client = OpenAI(api_key="sk-123", base_url="http://127.0.0.1:11434/invalid")
    client.chat.completions.create(
        model="qwen3.5:0.8b",
        messages=[{"role": "user", "content": "hi"}]
    )
except Exception as exc:
    print(f"Exception type: {type(exc)}")
    print(f"Exception string: '{exc}'")
