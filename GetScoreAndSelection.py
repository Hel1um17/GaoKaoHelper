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

    "targets": [
        "计算机科学与技术",
        "软件工程",
        "信息安全",
        "网络空间安全"
    ],

    "school_map_file": "schools.json",
    "school_list_file": "school.txt",

    "result_file": "result.jsonl",
    "checkpoint_file": "checkpoint.json",

    "sleep_min": 1.5,
    "sleep_max": 3.5,
    "pause_school": (3, 8),

    "empty_limit": 3,
    "timeout": 15,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Origin": "https://www.gaokao.cn",
    "Referer": "https://www.gaokao.cn/",
}


# ======================
# checkpoint
# ======================
def load_ck():
    if os.path.exists(CONFIG["checkpoint_file"]):
        return json.load(open(CONFIG["checkpoint_file"], "r", encoding="utf-8"))
    return {"i": 0}


def save_ck(i):
    json.dump({"i": i}, open(CONFIG["checkpoint_file"], "w", encoding="utf-8"))


# ======================
# 专业匹配
# ======================
def match_major(text):
    if not text:
        return None

    for t in CONFIG["targets"]:
        if t in text:
            return t

    if "计算机" in text:
        return "计算机科学与技术"
    if "软件" in text:
        return "软件工程"
    if "信息安全" in text:
        return "信息安全"
    if "网络空间" in text:
        return "网络空间安全"

    return None


# ======================
# 数据
# ======================
def load_school_map():
    d = json.load(open(CONFIG["school_map_file"], "r", encoding="utf-8"))
    return {v: k for k, v in d.items()}


def load_school_list():
    return [x.strip() for x in open(CONFIG["school_list_file"], "r", encoding="utf-8") if x.strip()]


# ======================
# request
# ======================
def fetch(session, sid, year):

    payload = {
        "local_province_id": CONFIG["province_id"],
        "page": 1,
        "platform": "2",
        "school_id": str(sid),
        "size": 20,
        "uri": "v1/school/special_score",
        "year": str(year),
    }

    try:
        r = session.post(CONFIG["api_url"], json=payload, headers=HEADERS, timeout=CONFIG["timeout"])
        data = r.json().get("data") or {}
        return data.get("item") or []
    except:
        return []


# ======================
# main
# ======================
def main():

    school_map = load_school_map()
    school_list = load_school_list()

    ck = load_ck()
    start = ck["i"]

    session = requests.Session()

    empty_streak = 0

    print(f"start from {start}")

    with open(CONFIG["result_file"], "a", encoding="utf-8") as f:

        for i in range(start, len(school_list)):

            name = school_list[i]
            sid = school_map.get(name)

            if not sid:
                continue

            print(f"\n[{i}] {name}")

            school_total = 0

            for y in CONFIG["years"]:

                items = fetch(session, sid, y)

                if not items:
                    print(f"  {y}: empty")
                    continue

                school_total += len(items)

                for it in items:

                    remark = it.get("remark") or ""
                    sp_name = it.get("sp_name") or ""

                    major = match_major(remark) or match_major(sp_name)
                    if not major:
                        continue

                    # ======================
                    # ⭐ 重点：完整记录
                    # ======================
                    rec = {
                        "school": name,
                        "year": y,
                        "major": major,

                        "score": it.get("min"),
                        "rank": it.get("min_section"),

                        # ⭐ 必须保留（你要求的）
                        "remark": remark,

                        # ⭐ 可选但强烈建议保留
                        "sp_name": sp_name,
                        "average": it.get("average"),
                        "diff": it.get("diff"),
                        "lq_num": it.get("lq_num"),
                    }

                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")

                f.flush()

                time.sleep(random.uniform(CONFIG["sleep_min"], CONFIG["sleep_max"]))

            # ======================
            # 风控判断
            # ======================
            if school_total == 0:
                empty_streak += 1
            else:
                empty_streak = 0

            save_ck(i + 1)

            pause = random.uniform(*CONFIG["pause_school"])
            print(f"sleep {pause:.1f}s")

            time.sleep(pause)

            if empty_streak >= CONFIG["empty_limit"]:
                print("\n🚨 疑似风控（连续空数据）")
                print("👉 请换IP后重新运行（会自动断点继续）")
                break


if __name__ == "__main__":
    main()