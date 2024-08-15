# config

cookies = {
    "UUkey": "f1ab01f2e720f921237c959c07c1016f",
    "eai-sess": "5l6c5kjb54vfqd1jbu5am2uvi0",
}

def json_or_exit(res):
    try:
        return res.json()
    except Exception as e:
        print(f"error fetching json: {e}")
        print(f"url: {res.url}")
        print(f"responce: {res.content}")
        exit(1)