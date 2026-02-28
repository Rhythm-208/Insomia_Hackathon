import requests
s = requests.Session()
r = s.get('http://localhost:8000/auth/check/')
print(r.json())
