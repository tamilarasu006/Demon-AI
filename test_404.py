import asyncio
from OpenDEMON.engine.ollama import OllamaEngine
from OpenDEMON.core.types import Message, Role

async def main():
    engine = OllamaEngine()
    engine._client.base_url = "http://127.0.0.1:11434/invalid"
    try:
        async for chunk in engine.stream([Message(role=Role.USER, content="hi")], model="qwen3.5:0.8b"):
            pass
    except Exception as exc:
        print(f"Exception type: {type(exc)}")
        print(f"Exception string: '{exc}'")

asyncio.run(main())
