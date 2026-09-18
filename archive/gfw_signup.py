import requests

response = requests.post(
    "https://data-api.globalforestwatch.org/auth/sign-up",
    json={
        "name": "Anuja",              # put your actual name
        "email": "anujajp.05@gmail.com"  # put your real email — you'll need to receive a password
    }
)

print("Status:", response.status_code)
print("Response:", response.json())