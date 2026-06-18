import asyncio

import aiohttp

from helpers import *

import requests
from get_keys import get_key

CLIENT_ID = get_key("twitchclient")
CLIENT_SECRET  = get_key("twitch")

url = "https://id.twitch.tv/oauth2/token"
params = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "client_credentials"
}

res = requests.post(url, params=params)
data = res.json()

access_token = data["access_token"]
written_name_cache = {}

last_game_dict = {}

def get_startup_statuses(users):
    global last_game_dict

    if(len(users) < 1):
        return {}

    params = build_params_for_category_check(users)

    res = requests.get(
        "https://api.twitch.tv/helix/streams",
        headers=get_headers(),
        params=params
    )

    current_statuses = {}

    for stream in res.json()["data"]:
        current_statuses[stream["user_login"]] = " is online and playing " + stream["game_name"]
        last_game_dict[stream["user_login"]] = stream["game_name"]

    for user in users:
        if(not user in current_statuses):
            current_statuses[user] = " is offline"
            last_game_dict[user] = "streamer-offline"
    return current_statuses

# async def get_latest_vod_link(user_login):


async def check_for_category_change(user_login):
    global last_game_dict

    if(len(user_login) < 1):
        return {}

    headers = get_headers()

    update_dict = {}
    no_updates = []

    params = build_params_for_category_check(user_login)

    async with aiohttp.ClientSession() as session:
        async with session.get(
                "https://api.twitch.tv/helix/streams",
                headers=headers,
                params=params
        ) as res:
            data = await res.json()

    for stream in data["data"]: # Online
        if not (last_game_dict[stream["user_login"]] == stream["game_name"]): # Online, game changed
            if(last_game_dict[stream["user_login"]] == "streamer-offline"):
                update_dict[stream["user_login"]] = " is now online and playing " + stream["game_name"]
                last_game_dict[stream["user_login"]] = stream["game_name"]
            else:
                update_dict[stream["user_login"]] = " is now playing " + stream["game_name"]
                last_game_dict[stream["user_login"]] = stream["game_name"]
        else:
            no_updates.append(stream["user_login"])

    for stream in last_game_dict:
        if (not stream in update_dict) and (not stream in no_updates): # Streamer offline
            if(last_game_dict[stream] != "streamer-offline"): # Streamer was online, but no longer online
                update_dict[stream] = " is now offline."
                last_game_dict[stream] = "streamer-offline"

    username_update_dict = {}
    for item in update_dict:
        username = get_twitch_username(item)
        username_update_dict[username] = update_dict[item]
        if(username == "xQc"):
            username_update_dict[username] = username_update_dict[username] + "\nUPDATE: xQc is now playing " + update_dict[item] + "!"

    return username_update_dict

def build_params_for_category_check(users):
    global last_game_dict
    param_list = []

    for user in users:
        if(not user in last_game_dict.keys()):
            last_game_dict[user] = "abc-123-offline"

        param_list.append(("user_login", user))

    return param_list

def get_twitch_username(user_login):
    if(user_login not in written_name_cache):
        headers = get_headers()
        params = {"login":user_login}

        res = requests.get(
            "https://api.twitch.tv/helix/users",
            headers=headers,
            params=params
        )
        data = res.json()["data"][0]
        written_name_cache[user_login] = data["display_name"]

    return written_name_cache[user_login]

def get_twitch_user_id(user_login):
    if(user_login not in written_name_cache):
        headers = get_headers()
        params = {"login":user_login}

        res = requests.get(
            "https://api.twitch.tv/helix/users",
            headers=headers,
            params=params
        )
        data = res.json()["data"][0]

    return data["id"]

def get_latest_vod(user_id):
    headers = {
        "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {access_token}"
    }

    params = {
        "user_id": user_id,
        "first": 1,
        "type": "archive"
    }

    res = requests.get(
        "https://api.twitch.tv/helix/videos",
        headers=headers,
        params=params
    )

    data = res.json()["data"]

    if data:
        latest_video = data[0]
        print(latest_video["title"])
        print(latest_video["url"])


def get_headers():
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }
    return headers

def set_game(streamer, game):
    global last_game_dict
    last_game_dict[streamer] = game


username = get_twitch_username("xqc")
id = get_twitch_user_id("xQc")
get_latest_vod(id)