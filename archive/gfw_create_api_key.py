import requests

ACCESS_TOKEN = "YOUR_GFW_ACCESS_TOKEN"

response = requests.post(
    "https://data-api.globalforestwatch.org/auth/apikey",
    headers={
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    },
    json={
        "alias": "ecoreason-hackathon",
        "email": "anujajp.05@gmail.com",     # same email you signed up with
        "organization": "Student Hackathon Project",
        "domains": []   # empty list = no domain restriction, fine for local dev/testing
    }
)

print("Status:", response.status_code)
print("Response:", response.json())