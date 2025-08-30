import requests
headers = {"x-api-key": "freight-broker-prod-20250828"}
response = requests.get("https://freight-broker-happyrobot.fly.dev/loads", headers=headers)
print(response.json())