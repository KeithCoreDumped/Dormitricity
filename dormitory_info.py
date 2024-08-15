# fetch dormitory info as json

import requests, json, datetime as dt
from config import cookies, json_or_exit


def fetch_dormitories(aria_id: str, part_id: str, floor_id: str):
    responce = requests.post(
        "https://app.bupt.edu.cn/buptdf/wap/default/drom",  # should be dorm though
        data={"areaid": aria_id, "partmentId": part_id, "floorId": floor_id},
        cookies=cookies,
    )
    res_json = json_or_exit(responce)
    # return list of dormitory names
    dorm_dict = dict()
    for dorm in res_json["d"]["data"]:
        name = dorm["dromName"]
        id = dorm["dromNum"]
        dorm_dict[name] = id
    return dorm_dict


def fetch_floors(aria_id: str, part_id: str):
    responce = requests.post(
        "https://app.bupt.edu.cn/buptdf/wap/default/floor",
        data={"areaid": aria_id, "partmentId": part_id},
        cookies=cookies,
    )
    res_json = json_or_exit(responce)
    floors = [x["floorName"] for x in res_json["d"]["data"]]
    floor_dict = dict()
    room_counter = 0
    for floor in floors:
        dorm_dict = fetch_dormitories(aria_id, part_id, floor)
        floor_dict[floor] = dorm_dict
        room_counter += len(dorm_dict)
        print(f"{len(dorm_dict)}, {room_counter}\r", end="", flush=True)
    return floor_dict, room_counter


def fetch_campus(area_id: str):
    responce = requests.post(
        "https://app.bupt.edu.cn/buptdf/wap/default/part",
        data={
            "areaid": area_id,
        },
        cookies=cookies,
    )

    res_json = json_or_exit(responce)
    data = res_json["d"]["data"]
    campus_dict = dict()
    room_counter = 0
    for d in data:
        partmentId = d["partmentId"]
        partmentName = d["partmentName"]
        floors, rooms = fetch_floors(area_id, partmentId)
        room_counter += rooms
        campus_dict[partmentName] = {"id": partmentId, "floors": floors}
    # dormitory_dict[name] = campus_dict
    return campus_dict, room_counter


def fetch_bupt():
    campus_list = [("1", "西土城"), ("2", "沙河")]
    dormitory_info = dict()
    for area_id, name in campus_list:
        campus_dict, rooms = fetch_campus(area_id)
        dormitory_info[name] = campus_dict
        dormitory_info[f"__{name}_rooms__"] = rooms
        print(f"{rooms} rooms in {name}")
    return dormitory_info


# main logic

begin = dt.datetime.now()

with open("dormitory_info.json", "wt", encoding="utf-8") as f:
    json.dump(fetch_bupt(), f)

end = dt.datetime.now()
duration = end - begin
print(f"time: {duration}")
