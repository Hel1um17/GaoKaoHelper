#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import random
import os

CONFIG = {
    "api_url": "https://api-gaokao.zjzw.cn/apidata/web",

    "province_id": "41",
    "years": list(range(2021, 2026)),

    "school_map_file": "schools.json",
    "school_list_file": "school.txt",

    "result_file": "result.jsonl",

    "pages": 5,

    "sleep_min": 1.2,
    "sleep_max": 2.5,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Origin": "https://www.gaokao.cn",
    "Referer": "https://www.gaokao.cn/",
}


# ======================
# key（必须和旧数据一致）
# ======================
def make_key(school_id, year, sp_name, remark):
    return f"{school_id}||{year}||{sp_name}||{remark}"


# ======================
# load school
# ======================
def load_school_map():
    d = json.load(open(CONFIG["school_map_file"], "r", encoding="utf-8"))
    return {v: k for k, v in d.items()}


def load_school_list():
    return [x.strip() for x in open(CONFIG["school_list_file"], "r", encoding="utf-8") if x.strip()]


# ======================
# fetch plan
# ======================
def fetch(session, sid, year, page):

    payload = {
        "local_province_id": CONFIG["province_id"],
        "page": page,
        "platform": "2",
        "school_id": str(sid),
        "size": 20,
        "uri": "v1/school/special_plan",
        "year": str(year),
    }

    try:
        r = session.post(CONFIG["api_url"], json=payload, headers=HEADERS, timeout=15)
        data = r.json().get("data") or {}
        return data.get("item") or []
    except:
        return []


# ======================
# load existing jsonl
# ======================
def load_existing():

    data = {}

    if not os.path.exists(CONFIG["result_file"]):
        return data

    with open(CONFIG["result_file"], "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)

                key = obj.get("key")
                if key:
                    data[key] = obj

            except:
                pass

    return data


# ======================
# main
# ======================
def main():

    school_map = load_school_map()
    school_list = load_school_list()

    session = requests.Session()

    cache = load_existing()
    print(f"loaded existing: {len(cache)}")

    for i, school_name in enumerate(school_list):

        sid = school_map.get(school_name)
        if not sid:
            continue

        print(f"\n[{i}] {school_name}")

        for year in CONFIG["years"]:

            for page in range(1, CONFIG["pages"] + 1):

                items = fetch(session, sid, year, page)

                if not items:
                    break

                for it in items:

                    sp_name = it.get("sp_name") or ""
                    remark = it.get("remark") or ""

                    key = make_key(sid, year, sp_name, remark)

                    num = it.get("num")

                    # ======================
                    # ⭐ 只更新 num
                    # ======================
                    if key in cache:
                        cache[key]["num"] = num
                    else:
                        # 如果旧数据没有这个 key，也补进去
                        cache[key] = {
                            "key": key,
                            "school_id": sid,
                            "school": school_name,
                            "year": year,
                            "sp_name": sp_name,
                            "remark": remark,
                            "num": num
                        }

                time.sleep(random.uniform(CONFIG["sleep_min"], CONFIG["sleep_max"]))

    # ======================
    # 写回文件（关键）
    # ======================
    with open(CONFIG["result_file"], "w", encoding="utf-8") as f:
        for v in cache.values():
            f.write(json.dumps(v, ensure_ascii=False) + "\n")

    print("\nDONE")


if __name__ == "__main__":
    main()