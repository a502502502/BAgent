from services.http_client import HttpClient

client = HttpClient()

html = client.get("https://www.google.com")

print(f"HTML ricevuto: {len(html)} caratteri")

client.close()