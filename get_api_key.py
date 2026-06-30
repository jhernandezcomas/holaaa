import os
import requests

api_key_id = os.environ["API_KEY_ID"]
oauth_token = os.environ["ANTHROPIC_OAUTH_TOKEN"]

response = requests.get(
    f"https://api.anthropic.com/v1/organizations/api_keys/{api_key_id}",
    headers={
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "oauth-2025-04-20",
        "Authorization": f"Bearer {oauth_token}",
    },
)

response.raise_for_status()
print(response.json())
