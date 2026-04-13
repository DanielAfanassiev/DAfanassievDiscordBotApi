import datetime
import json
import os
import re
import time

CACHE_DIR = "cache/"

def log(message, log_file = "log.txt"):
    date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message = date + ": " + message
    if log_file == "log.txt":
        print(message.encode("utf-8", errors="ignore").decode("utf-8"))
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def write_to_cache(cache_dict, filename):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache_dict, f, indent=4)
    log("Cache written " + filename, "cachelog.txt")


def read_from_cache(filename):
    path = os.path.join(CACHE_DIR, filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        log("Cache not found " + filename)
        return {}
    except json.JSONDecodeError:
        log(f"Cache corrupted: {filename}")
        return {}

def is_cache_valid(last_retrieval, ttl_minutes):
    return time.time() - last_retrieval < ttl_minutes * 60

def remove_special_chars(text):
    return re.sub(r"[^A-Za-z0-9]", " ", text)