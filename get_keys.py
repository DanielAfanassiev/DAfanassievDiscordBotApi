keys = {}

API_KEYS_DIR = "apikeys"

def get_key(key):
    return keys[key]

def load_keys():
    global keys
    with open(f"{API_KEYS_DIR}/keys.csv") as f:
        rawLines = [line.strip() for line in f if line.strip()]
        for line in rawLines:
            keys[line[:line.find(',')]] = line[(line.find(',')+1):]

def get_api_key_dir():
    return f"{API_KEYS_DIR}"

load_keys()