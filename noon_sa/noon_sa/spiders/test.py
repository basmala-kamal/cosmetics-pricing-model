import requests

API_KEY = "d3f13b11a6dc4c05b170b31655780006"
target_url = "https://www.noon.com/saudi-en/search/?q=tint&page=1"

params = {
    "url": target_url,
    "x-api-key": API_KEY,
    "browser": True,
    "proxy_type": "residential"
}

response = requests.get("https://api.scrapingant.com/v2/general", params=params, timeout=120)

print("Status Code:", response.status_code)
print("Preview:\n", response.text[:500])
