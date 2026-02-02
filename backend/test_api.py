import requests

print("Uploading...")
files = {'file': open('../test.pdf', 'rb')}
r = requests.post('http://localhost:8000/upload', files=files)
print(f"Upload Status: {r.status_code}")
print(r.text)

print("Chatting...")
r = requests.post('http://localhost:8000/chat', json={'question': 'What is Antigravity?'})
print(f"Chat Status: {r.status_code}")
print(r.text)
