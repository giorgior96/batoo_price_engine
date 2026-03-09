import httpx
from config import ZYTE_PROXY

def save_yachtall_page():
    proxy = ZYTE_PROXY
    url = "https://www.yachtall.com/it/barche/barche-usate?pg=2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    with httpx.Client(proxy=proxy, verify=False, follow_redirects=True) as client:
        response = client.get(url, headers=headers, timeout=60.0)
        with open("yachtall_sample_p2.html", "w") as f:
            f.write(response.text)
        print(f"Saved {url} to yachtall_sample_p2.html")

if __name__ == "__main__":
    save_yachtall_page()
