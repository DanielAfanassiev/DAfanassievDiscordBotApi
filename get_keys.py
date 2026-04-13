keys = {}

def get_key(key):
    return keys[key]

def load_keys():
    global keys
    with open("apikeys/keys.csv") as f:
        rawLines = [line.strip() for line in f if line.strip()]
        for line in rawLines:
            keys[line[:line.find(',')]] = line[(line.find(',')+1):]

load_keys()