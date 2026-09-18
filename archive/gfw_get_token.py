import requests

response = requests.post(
    "https://data-api.globalforestwatch.org/auth/token",
    data={  # note: this endpoint typically wants form data, not JSON
        "username": "anujajp.05@gmail.com",  # the email you signed up with
        "password": "Chicafeliz36"        # the password you just created
    }
)

print("Status:", response.status_code)
print("Response:", response.json())