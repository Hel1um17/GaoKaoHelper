import requests
import json
import time
import os

URL = "https://api-gaokao.zjzw.cn/apidata/web"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

TARGETS = [
    "计算机科学与技术",
    "软件工程",
    "信息安全",
    "网络空间安全"
]


# ---------------------------
# 专业匹配
# ---------------------------
def match_major(text):
    if not text:
        return None
    for t in TARGETS:
        if t in text:
            return t
    return None


# ---------------------------
# school映射
# ---------------------------
def load_school_map():
    with open("schools.json", "r", encoding="utf-8") as f:
        id_to_name = json.load(f)
    return {v: k for k, v in id_to_name.items()}


# ---------------------------
# 读取断点
# ---------------------------
def load_progress():
    if not os.path.exists("progress.txt"):
        return set()
    with open("progress.txt", "r", encoding="utf-8") as f:
        return set([x.strip() for x in f if x.strip()])


# ---------------------------
# 写断点
# ---------------------------
def save_progress(name):
    with open("progress.txt", "a", encoding="utf-8") as f:
        f.write(name + "\n")


# ---------------------------
# 流式写入 JSONL
# ---------------------------
def write_jsonl(obj):
    with open("result.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ---------------------------
# 分数接口
# ---------------------------
def fetch_score(school_id, year):
    payload = {
        "autosign": "",
        "like_spname": "",
        "local_batch_id": "14",
        "local_province_id": "41",
        "local_type_id": "2073",
        "page": 1,
        "platform": "2",
        "school_id": str(school_id),
        "sg_xuanke": "",
        "signsafe": "",
        "size": 10,
        "special_group": "",
        "uri": "v1/school/special_score",
        "year": str(year)
    }

    r = requests.post(URL, json=payload, headers=HEADERS, timeout=15)
    return r.json().get("data", {}).get("item", [])


# ---------------------------
# 招生计划接口
# ---------------------------
def fetch_plan(school_id, year):
    payload = {
        "autosign": "",
        "like_spname": "",
        "local_batch_id": "7",
        "local_province_id": "41",
        "local_type_id": "1",
        "page": 1,
        "platform": "2",
        "school_id": str(school_id),
        "sg_xuanke": "",
        "signsafe": "",
        "size": 10,
        "special_group": "",
        "uri": "v1/school/special_plan",
        "year": str(year)
    }

    r = requests.post(URL, json=payload, headers=HEADERS, timeout=15)
    return r.json().get("data", {}).get("item", [])


# ---------------------------
# 主流程（核心）
# ---------------------------
def run():
    school_map = load_school_map()
    done = load_progress()
    school_list = open("school.txt", "r", encoding="utf-8").read().splitlines()

    for school_name in school_list:

        if school_name in done:
            print(f"[跳过] {school_name}")
            continue

        school_id = school_map.get(school_name)

        if not school_id:
            print(f"[未找到] {school_name}")
            continue

        print(f"\n=== {school_name} ===")

        for year in range(2021, 2026):

            try:
                score_items = fetch_score(school_id, year)
                plan_items = fetch_plan(school_id, year)

                # ---- score ----
                for item in score_items:
                    major = match_major(item.get("remark")) or match_major(item.get("sp_name"))

                    if major:
                        write_jsonl({
                            "school": school_name,
                            "major": major,
                            "year": year,
                            "score": item.get("min"),
                            "rank": item.get("min_section"),
                            "num": None
                        })

                # ---- plan ----
                for item in plan_items:
                    major = match_major(item.get("remark")) or match_major(item.get("sp_name"))

                    if major:
                        write_jsonl({
                            "school": school_name,
                            "major": major,
                            "year": year,
                            "score": None,
                            "rank": None,
                            "num": item.get("num")
                        })

                time.sleep(1)

            except Exception as e:
                print(f"[错误]{school_name}-{year}: {e}")

        # 标记完成
        save_progress(school_name)
        print(f"[完成] {school_name}")


if __name__ == "__main__":
    run()