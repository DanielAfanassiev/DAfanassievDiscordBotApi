import requests
import get_keys
from helpers import *
import spreadsheet_writer

CSFLOAT_API_URL = "https://csfloat.com/api/v1/listings"

MINUTES = 0
HOURS = 0
DAYS = 1

QUERY_THRESHOLD_MINUTES = DAYS * (60*24) + HOURS * 60 + MINUTES

failed_items = ""
cooldown_override = False
cached_items_dict = read_from_cache("cached_items_dict.txt") # structure {key: item_name, {key: price, key: last_retrieval}}
cached_steam64_ids_dict = read_from_cache("cached_steam64_ids_dict.txt")

def get_lowest_avg_price(item_name, count=20):
    global cached_items_dict
    global cooldown_override

    if cached_items_dict and item_name in cached_items_dict:
        last_retrieval_time = cached_items_dict[item_name]["last_retrieval_time"]
        if is_cache_valid(last_retrieval_time, QUERY_THRESHOLD_MINUTES) or cooldown_override:
            log("Using cached item for " + item_name)
            return cached_items_dict[item_name]["avg_price"]
        else:
            log("Not using cached item for " + item_name + ", too old.")
    log("Calling API for " + item_name)
    params = {
        "market_hash_name": item_name,
        "sort_by": "lowest_price",
        "type": "buy_now",
        "limit": 50
    }

    headers = {
    "Authorization": get_keys.get_key("csfloat"),
    "Content-Type": "application/json"
    }

    cooldown_override = False
    try:
        response = requests.get(CSFLOAT_API_URL, params=params, headers=headers)
        response.raise_for_status()
    except Exception as e:
        if("429" in str(e)):
            print("still on cooldown")
            cooldown_override = True

    if(not cooldown_override):
        remaining = int(response.headers.get("x-ratelimit-remaining", 0) or 0)
        reset_time = int(response.headers.get("x-ratelimit-reset", 0) or 0)
        reset = datetime.datetime.fromtimestamp(reset_time).strftime("%Y-%m-%d %H:%M:%S")

        now = int(time.time())
        seconds_left = reset_time - now

        log(str(remaining) + " calls to csfloat remaining until " + str(reset) + ". (" + str(seconds_left/60) + " minutes left)")

        data = response.json()

        listings = data.get("data", [])

        if not listings:
            return None

        prices = sorted([listing["price"] for listing in listings])
        lowest = prices[:count]

        lowest = get_lowest_within_10_pct(lowest)

        if not lowest:
            return None

        avg_price = (sum(lowest) / len(lowest)) / 100
    else:
        if(item_name in cached_items_dict):
            avg_price = cached_items_dict[item_name]["avg_price"]
        else:
            return 0

    print(f"{item_name}: {avg_price:.2f}")

    cached_items_dict[item_name] = {"avg_price": round(avg_price,2), "last_retrieval_time": int(time.time())}
    write_to_cache(cached_items_dict, "cached_items_dict.txt")

    return round(avg_price,2)


def written_name_to_actual_name(written_name):
    simple_cases = ["Fever",
                    "Fracture",
                    "Gamma 2",
                    "Gamma",
                    "Glove",
                    "Prisma",
                    "Recoil"]
        
    cases_dict = {
        "Phoenix" : "Operation Phoenix Weapon Case",
        "D&N" : "Dreams & Nightmares Case"}

    if(written_name in simple_cases):
        return written_name + " Case"
    else:
        return cases_dict[written_name]

def write_results_to_file(fullstring):
    #write items to file
    #items = dict, key = name, value[0] = count, value[1] = price
    filename = "cases-value-" + get_date_for_filename()
    try:
        os.mkdir("cases_output")
    except FileExistsError:
        pass
    except:
        print("Other error")
        return
    f = open("cases_output/" + filename + ".txt", "x", encoding="utf-8")
    f.write(fullstring)

def get_cases_item_dict():
    with open("Cases.txt", "r") as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    cases = {}

    for line in raw_lines:
        count = int(line[line.rfind(" ") + 1:])
        case_name = written_name_to_actual_name(line[:line.find(":")])
        cases[case_name] = (count, get_lowest_avg_price(case_name))

    return cases


def run_case_price_check():
    cases = get_cases_item_dict()
    return item_dict_to_string(cases, True)

def get_inventory(steam_url):
    steam64_id = parse_steam_url(steam_url)

    url = f"https://steamcommunity.com/inventory/{steam64_id}/730/2"
    data = requests.get(url).json()

    items = []

    desc_map = {
        (d["classid"], d["instanceid"]): d
        for d in data.get("descriptions", [])
    }

    for asset in data.get("assets", []):
        key = (asset["classid"], asset["instanceid"])
        desc = desc_map.get(key)

        if desc and desc.get("marketable") == 1:
            items.append(desc["market_hash_name"])

    return items #Raw list, may include duplicate items

def get_date_for_filename():
    current_date = datetime.datetime.now()
    year = current_date.strftime("%Y")
    month = current_date.strftime("%m")
    day = current_date.strftime("%d")
    hour = current_date.strftime("%H")
    minute = current_date.strftime("%M")
    second = current_date.strftime("%S")
    return year + "-" + month + "-" + day +"--" + hour + "-" + minute +"-" + second

def parse_steam_url(url):
    if "/id/" in url:
        start_of_username = url.rfind("/id/") + len("/id/")
        end_of_username = url[start_of_username:].find("/") + start_of_username
        if end_of_username == (start_of_username-1):
            vanity = url[start_of_username:]
        else:
            vanity = url[start_of_username:end_of_username]
        return get_steam64_via_vanity(vanity)
    else:
        start_of_id = url.rfind("/profiles/") + len("/profiles/")
        end_of_id = url[start_of_id:].find("/") + start_of_id

        if end_of_id == (start_of_id - 1):
            return url[start_of_id:]
        else:
            return url[start_of_id:end_of_id]


def get_steam64_via_vanity(vanity):
    if(not vanity in cached_steam64_ids_dict):
        url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"

        params = {
            "key": get_keys.get_key("steam"),
            "vanityurl": vanity
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        cached_steam64_ids_dict[vanity] = response.json().get("response").get("steamid")
        write_to_cache(cached_steam64_ids_dict, "cached_steam64_ids_dict.txt")
        log("Cached " + vanity + " steam ID as " + cached_steam64_ids_dict[vanity])
    return cached_steam64_ids_dict[vanity]

def inventory_to_item_dict(inventory, get_value):
    item_dict = {}

    for item in inventory:
        if item not in item_dict:
            if(get_value):
                avg_price = get_lowest_avg_price(item)
            else:
                avg_price = -1
            item_dict[item] = (1, avg_price)
        else:
            item_dict[item] = (item_dict[item][0] + 1, item_dict[item][1])

    return item_dict

def item_dict_to_string(item_dict, price_included):
    item_string = ""
    global failed_items
    if(price_included):
        sorted_item_list = sort_item_dict(item_dict)
    else:
        sorted_item_list = get_item_list_from_dict(item_dict)
    total_value = 0
    for item in sorted_item_list:
        item_string += (item[0] + ":\n")
        more_than_1 = item[1] > 1
        if(more_than_1):
            item_string += "   Count: " + str(item[1]) + "\n"
        if(price_included):
            if(more_than_1):
                item_string += "   Value/item: $" + str(item[2]) + "\n" "   Combined value: $" + str(round(float(item[1]) * item[2], 2))
            else:
                item_string +=  "   Value: $" + str(round(float(item[1]) * item[2], 2))

        item_string +=  "\n\n"

        total_value += round(float(item[1]) * item[2] ,2)

    if(price_included):
        item_string = item_string + "\nTotal value: $" + str(round(total_value, 2)) + " USD"
        if(len(failed_items) > 0):
            item_string += "\n\nFailed to get prices for the following items: " + failed_items

    return item_string

def get_item_list_from_dict(item_dict):
    item_list = []
    for item in item_dict:
        item_list.append((item, item_dict[item][0], item_dict[item][1]))
    return item_list

def sort_item_dict(item_dict):
    global failed_items
    failed_items = ""
    sorted_item_list = []
    for item in list(item_dict.keys()):
        if item_dict[item][1] is None:
            print(item + " failed")
            failed_items += item + ", "
            item_dict.pop(item)

    while(len(item_dict) > 0):
        max_item = get_max_value_item(item_dict)
        sorted_item_list.append((max_item, item_dict[max_item][0], item_dict[max_item][1]))
        item_dict.pop(max_item)

    return sorted_item_list

def get_max_value_item(item_dict):
    max_item = ""
    max_value = 0
    for item in item_dict:
        if item_dict[item][1] > max_value:
            max_value = item_dict[item][1]
            max_item = item

    return max_item

def get_inventory_value(steam_profile_url):
    inventory = get_inventory(steam_profile_url)

    steam_64 = parse_steam_url(steam_profile_url)

    item_dict = inventory_to_item_dict(inventory, True)
    spreadsheet_writer.add_spreadsheet_datapoint_inventory(item_dict, steam_64)
    spreadsheet_writer.create_inventory_spreadseet(steam_64, [0,1])
    return item_dict_to_string(item_dict, True)

def get_inventory_no_value(steam_profile_url):
    inventory = get_inventory(steam_profile_url)
    inventory_item_dict = inventory_to_item_dict(inventory, False)
    final_string = item_dict_to_string(inventory_item_dict, False)
    return final_string

def get_lowest_within_10_pct(listings):
    lowest = min(listings)
    within_10_pct = []
    for item in listings:
        if item <= lowest * 1.1:
            within_10_pct.append(item)

    return within_10_pct

def cleanup_name(item_name, max_len = 999999999, include_end = False):
    item_name = shorten_wear(item_name)
    item_name = item_name.replace("Sticker | ", "")
    if(include_end):
        four_off_end = len(item_name) - 4
        end = item_name[four_off_end:]
        chars_from_start = max_len - 4
        item_name = item_name[:chars_from_start] + end

    else:
        item_name = item_name[:max_len]

    item_name = item_name.replace("StatTrak", "ST")
    return item_name

def shorten_wear(item_name):
    wear_dict = {"Factory New": "FN",
                 "Minimal Wear": "MW",
                 "Field Tested": "FT",
                 "Well Worn": "WW",
                 "Battle Scarred": "BS"}
    for item in wear_dict:
        if(item in item_name):
            item_name = item_name.replace(item, wear_dict[item])
            return item_name

    else:
        return item_name

if __name__ == "__main__":
    steam_user_url = "https://steamcommunity.com/id/danfrommcdonalds/"
    get_inventory(steam_user_url)
    
