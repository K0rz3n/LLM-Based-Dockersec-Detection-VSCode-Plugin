from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
import threading
import torch
import json
import requests
# ----- GPU
# tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-14B-Instruct", trust_remote_code=True)
# model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-14B-Instruct", trust_remote_code=True).cuda().eval()

# def generate_stream(prompt: str):
#     inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
#     streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

#     thread = threading.Thread(target=model.generate, kwargs=dict(
#         **inputs, streamer=streamer, max_new_tokens=1024, do_sample=True, temperature=0.7
#     ))
#     thread.start()

#     for chunk in streamer:
#         yield chunk

# ------ MAC

# # 加载模型和 tokenizer
# model_name = "Qwen/Qwen2.5-Coder-7B-Instruct"

# tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
# model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)

# # ✅ 加速模型执行
# if hasattr(torch, "compile"):
#     model = torch.compile(model)

# # ✅ MPS 优化：注意仍有部分操作较慢
# device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
# model.to(device).eval()

# def generate_stream(prompt: str, buffer_size=10):
#     inputs = tokenizer(prompt, return_tensors="pt")
#     inputs = {k: v.to(device) for k, v in inputs.items()}

#     streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

#     thread = threading.Thread(target=model.generate, kwargs=dict(
#         **inputs,
#         streamer=streamer,
#         max_new_tokens=512,  # ✅ 减小 token 数，减少延迟
#         do_sample=True,
#         temperature=0.7,
#         top_k=50,
#         top_p=0.9,
#         repetition_penalty=1.1,
#     ))
#     thread.start()

#     buffer = []
#     for token in streamer:
#         buffer.append(token)
#         if len(buffer) >= buffer_size:
#             yield "".join(buffer)
#             buffer = []
#     if buffer:
#         yield "".join(buffer)


def generate_stream(prompt: str, model: str = "qwen2.5-coder:14b", buffer_size=10):
    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 1.5,
            "top_k": 20,
            "top_p": 0.8,
            "repeat_penalty": 1.1
        }
    }

    buffer = []

    with requests.post(url, headers=headers, json=data, stream=True) as response:
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode("utf-8"))
                text = chunk.get("response", "")
                if chunk.get("done", False):
                    break
                buffer.append(text)
                if len(buffer) >= buffer_size:
                    yield "".join(buffer)
                    buffer = []
        if buffer:
            yield "".join(buffer)