
import json
import ollama
 
MODEL_NAME = "qwen3.5:4b"
 
 
def ask_llm(system_prompt: str, user_input: str, history: list = None) -> dict:
    messages = [{"role": "system", "content": system_prompt}]
 
    if history:
        messages.extend(history)
 
    messages.append({"role": "user", "content": user_input})
 
    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        format="json",
        options={"temperature": 0.2}
    )
 
    content = response["message"]["content"]
 
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {"action": "error", "params": {}, "reply": "Failed to parse model output."}
 
    if "action" not in parsed:
        parsed["action"] = "error"
    if "params" not in parsed:
        parsed["params"] = {}
    if "reply" not in parsed:
        parsed["reply"] = ""
 
    return parsed
 