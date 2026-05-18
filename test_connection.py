import litellm

response = litellm.completion(
    model="ollama/phi3:mini",
    api_base="http://localhost:11434",
    messages=[{"role": "user", "content": "Say hello in one sentence"}]
)

print(response.choices[0].message.content)
