import requests

base_url = "http://127.0.0.1:8000"

print("Registering...")
res = requests.post(f"{base_url}/v1/auth/register", json={
    "name": "Test User",
    "email": "test@example.com",
    "password": "Password123!"
})
print("Register response:", res.status_code, res.text)

print("Logging in...")
res = requests.post(f"{base_url}/v1/auth/login", json={
    "email": "test@example.com",
    "password": "Password123!"
})
print("Login response:", res.status_code, res.text)

if res.status_code == 200:
    token = res.json()["access_token"]
    print("Getting me...")
    res = requests.get(f"{base_url}/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    print("Me response:", res.status_code, res.text)
