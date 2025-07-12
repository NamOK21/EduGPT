import requests

response = requests.post("http://localhost:1234/v1/chat/completions", json={
    "model": "llama-3.2-3b-instruct",
    "messages": [
        {"role": "system", "content": "Bạn là trợ lý thông minh."},
        {"role": "user", "content": "Xin chào, bạn có khoẻ không?"}
    ],
    "temperature": 0.5
})

print(response.status_code)
print(response.json())