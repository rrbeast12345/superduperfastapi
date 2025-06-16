import requests

url = "http://localhost:8000/verify_identity"
data = {
  "id_number": "string",
  "name": "string",
  "dob": "string"
}

response = requests.post(url, json=data)
print(response.json())