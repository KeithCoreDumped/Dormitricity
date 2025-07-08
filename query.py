import json, sys, argparse
from datetime import datetime
from urllib.parse import parse_qs
import requests
from storage import csv_storage
import plot
import notify

mail_config = {
    "mail_host": "smtp.exmail.qq.com",
    "mail_port": 465,
    "mail_user": "",
    "mail_pass": "",
    "sender": "",
    "receivers": [""],
    "mail_notify": False,  # whether to send email notification
    "force_notify": False,  # whether to send email notification even if not low power
}


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
        except KeyError as exc:
            available_keys: list[str] = list(self.keys())
            available_keys = list(  # filter out reserved keys
                filter(
                    lambda s: not s.startswith("__") and not s.endswith("__"),
                    available_keys,
                )
            )
            raise bad_query(
                f"attribute '{key}' not found. available: {sorted(available_keys)}"
            ) from exc

def json_or_exit(res):
    try:
        return res.json()
    except ValueError as e:
        print(f"error fetching json: {e}")
        print(f"url: {res.url}")
        print(f"responce: {res.content}")
        exit(1)


def do_query(query_str: str, q_passphrase: str, q_cookies: dict):
    # check if such room exists
    query_name = query_str.split("@")
    query_str = ""
    room_name = ""
    if len(query_name) < 2:
        print("unexpected query string format")
        show_help_exit()
    if len(query_name) == 2:
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
        sys.exit(1)

    # query the api
    print("querying ...", end="", flush=True)
    response = requests.post(
        "https://app.bupt.edu.cn/buptdf/wap/default/search",
        data={
            "partmentId": dormitory_info[campus][partment]["id"],
            "floorId": floor,
            "dromNumber": room_id,
            "areaid": str(int(campus != "西土城") + 1),
        },
        cookies=q_cookies,
        timeout=10,
    )
    print(" done")

    res: dict = json_or_exit(response)

    data = res["d"]["data"]
    remain = data["surplus"] + data["freeEnd"]  # 剩余电量 + 剩余赠送电量
    time = datetime.fromisoformat(data["time"])

    # append query result to csv
    cs = csv_storage(room_name, q_passphrase)
    cs.append(f"{remain}, {time}, {datetime.now()}\n")

    print(f"successfully saved to {cs.filename}")
    plot.plot(cs)

    if (remain < 5 and mail_config["mail_notify"]) or mail_config["force_notify"]:
        mail_config["receivers"] = receiver_dict.get(room_name, [mail_config["sender"]])
        ret = notify.mail_notification(
            mail_config=mail_config,
            subject=f"宿舍电量预警: {room_name}",
            body=f"当前电量: {remain}度\n时间: {time}" + "<img src='{img0}'><img src='{img1}'>",
            image_paths=[f"{cs.filepath}/recent.png", f"{cs.filepath}/watts.png"],
        )
        if ret:
            print(f"notification sent to {', '.join(mail_config['receivers'])}")
        else:
            raise RuntimeError(
                f"failed to send notification to {', '.join(mail_config['receivers'])}")

def show_help_exit():
    print("usage: dormitricity query -q 'campus.partment.floor.room@room_name' -p passphrase -c cookies [-m mail_address&mail_pass&smtp_host&force_notify] [-r room_name,mail1&mail2;room_name2,mail1&mail2]")
    print("example: dormitricity query -q '西土城.东区.1.101@101' -p 'your_passphrase' -c 'UUKey=value1&eai-sess=value2' -m 'mail_address&mail_pass&smtp_host&1' -r '101,mail1&mail2;102,mail3'")
    sys.exit(1)

# main logic

parser = argparse.ArgumentParser(description="Dormitricity Query Tool")
parser.add_argument("-q", "--query", type=str, required=True,
                    help="Query string in the format 'campus.partment.floor.room@room_name'")
parser.add_argument("-p", "--passphrase", type=str, required=True,
                    help="Passphrase for the query")
parser.add_argument("-c", "--cookies", type=str, required=True,
                    help="Cookies in URL-encoded format, e.g., 'UUKey=value1&eai-sess=value2'")
parser.add_argument("-m", "--mail", type=str, nargs='?', default="",
                    help="Email address for notifications, " \
                    "e.g., 'mail_address&mail_pass&smtp_host&force_notify', (optional)")
parser.add_argument("-r", "--receivers", type=str, nargs='?', default="",
                    help="Custom receivers for specific rooms "
                    "in the format 'room_name,mail1&mail2;room_name2,mail1&mail2' (optional)")
args = parser.parse_args()

# load dormitory info
print("loading dormitory info ...", end="", flush=True)
with open("dormitory_info.json", "rt", encoding="utf-8") as f:
    dormitory_info: dict = verbose_dict(json.load(f))
print(" done")


passphrase = args.passphrase

cookies = {k: v[0] for k, v in parse_qs(args.cookies).items()}

mail_config["mail_user"] = args.mail.split("&")[0] if args.mail else ""
mail_config["mail_pass"] = args.mail.split("&")[1] if args.mail else ""
mail_config["mail_host"] = args.mail.split("&")[2] if args.mail else ""
mail_config["sender"] = mail_config["mail_user"]
mail_config["mail_notify"] = True if args.mail else False
mail_config["force_notify"] = args.mail.split("&")[3] in ["1", "true", "yes"] if args.mail else False

print("mail configuration:"
      f"\n  user: {mail_config['mail_user']}\n  host: {mail_config['mail_host']}\n  notify: {mail_config['mail_notify']}\n  force notify: {mail_config['force_notify']}")

receiver_dict = {}
if args.receivers:
    # room_name1,mail1&mail2;room_name2,mail1&mail2
    receiver_list = args.receivers.split(";")
    for name_and_mails in receiver_list:
        name, mails = name_and_mails.split(",", 1)
        mails = mails.split("&")
        receiver_dict[name] = mails
    print("receiver configuration:")
    for room_name, mails in receiver_dict.items():
        print(f"  {room_name}: {', '.join(mails)}")


for qs in args.query.split(","):
    do_query(qs, passphrase, cookies)
