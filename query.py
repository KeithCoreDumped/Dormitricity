import requests, os, json, sys
from datetime import datetime, timedelta
from storage import csv_storage
import plot
from urllib.parse import parse_qs


class bad_query(Exception):
    # subclass but acts exactly as the base class
    pass


class verbose_dict(dict):
    def __getitem__(self, key):
        try:
            res = super().__getitem__(key)
            if isinstance(res, dict) and not isinstance(res, verbose_dict):
                return verbose_dict(res)
            return res
        except KeyError:
            available_keys: list[str] = list(self.keys())
            available_keys = list(  # filter out reserved keys
                filter(
                    lambda s: not s.startswith("__") and not s.endswith("__"),
                    available_keys,
                )
            )
            raise bad_query(
                f"attribute '{key}' not found. available: {sorted(available_keys)}"
            )


def json_or_exit(res):
    try:
        return res.json()
    except Exception as e:
        print(f"error fetching json: {e}")
        print(f"url: {res.url}")
        print(f"responce: {res.content}")
        exit(1)


def do_query(query_str: str, passphrase: str, cookies: dict):
    # check if such room exists
    query_name = query_str.split("@")
    if len(query_name) != 2:
        print("no room name provided")
        show_help_exit()
    query_str, room_name = query_name
    if not room_name:
        print("empty room name")
        show_help_exit()
    cpfr = query_str.split(".")
    if len(cpfr) != 4:
        print("invalid query string")
        show_help_exit()
    campus, partment, floor, room = cpfr
    try:
        room_id = dormitory_info[campus][partment]["floors"][floor][room]
    except bad_query as e:
        print(f"bad query: {e}")
        exit(1)

    # query the api
    print(f"querying ...", end="", flush=True)
    responce = requests.post(
        "https://app.bupt.edu.cn/buptdf/wap/default/search",
        data={
            "partmentId": dormitory_info[campus][partment]["id"],
            "floorId": floor,
            "dromNumber": room_id,
            "areaid": str(int(campus != "西土城") + 1),
        },
        cookies=cookies,
    )
    print(f" done")

    res: dict = json_or_exit(responce)

    data = res["d"]["data"]
    remain = data["surplus"] + data["freeEnd"]  # 剩余电量 + 剩余赠送电量
    time = datetime.fromisoformat(data["time"])

    # append query result to csv
    cs = csv_storage(room_name, passphrase)
    cs.append(f"{remain}, {time}, {datetime.now()}\n")

    print(f"successfully saved to {cs.filename}")
    plot.plot(cs)


def show_help_exit():
    print("usage: query.py <query_str>[,query_str2,...] <passphrase> <cookies>")
    print(
        "example: query.py 西土城.学五楼.3.5-312-节能蓝天@学五-312宿舍,沙河.沙河校区雁北园A楼.1层.A楼102@沙河A102宿舍 example_passphrase UUkey=xxx&eai-sess=yyy"
    )
    exit(1)


# main logic

if len(sys.argv) != 4:
    print("invalid arguments.")
    show_help_exit()

# load dormitory info
print(f"loading dormitory info ...", end="", flush=True)
with open("dormitory_info.json", "rt", encoding="utf-8") as f:
    dormitory_info: dict = verbose_dict(json.load(f))
print(f" done")

passphrase = sys.argv[2]

cookies = {k: v[0] for k, v in parse_qs(sys.argv[3]).items()}

for qs in sys.argv[1].split(","):
    do_query(qs, passphrase, cookies)
