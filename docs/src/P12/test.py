from openai import OpenAI

client = OpenAI(api_key="g4a-H4FGnkOh5tj5DiL1TgOL6HdezWrNlQlBICt", base_url="https://api.gpt4-all.xyz/v1")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "List the best 5 books for a python developer"}],
    stream=False,
)

print(response.choices[0].message.content)