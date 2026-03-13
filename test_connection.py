import socket
import requests
import sys


def test_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


print("Testing port 8000 on various hosts...")
hosts = ["127.0.0.1", "localhost", "0.0.0.0", "::1"]
for host in hosts:
    if test_port(host, 8000):
        print(f"  {host}:8000 - OPEN")
    else:
        print(f"  {host}:8000 - CLOSED")

print("\nTrying HTTP request to 127.0.0.1:8000/api/health")
try:
    response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
    print(f"  Status: {response.status_code}, Response: {response.text[:100]}")
except Exception as e:
    print(f"  Error: {e}")

print("\nTrying HTTP request to localhost:8000/api/health")
try:
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    print(f"  Status: {response.status_code}, Response: {response.text[:100]}")
except Exception as e:
    print(f"  Error: {e}")
