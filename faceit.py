import requests
import os
from helpers import log
from get_keys import get_key

API_KEY = get_key("faceit")

BASE_HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

DOWNLOAD_DIR = "demos"


def ensure_download_dir():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_player_id(username):
    url = "https://open.faceit.com/data/v4/players"
    params = {"nickname": username}

    res = requests.get(url, headers=BASE_HEADERS, params=params)
    res.raise_for_status()

    data = res.json()
    return data["player_id"]


def get_match_history(player_id, game="cs2"):
    url = f"https://open.faceit.com/data/v4/players/{player_id}/history"
    params = {"game": game}

    res = requests.get(url, headers=BASE_HEADERS, params=params)
    res.raise_for_status()

    return res.json()["items"]


def get_demo_download_url(match_id):
    """
    This calls the same internal endpoint your browser uses
    to get the signed demo download URL.
    """
    url = "https://www.faceit.com/api/download/v2/demos/download-url"

    params = {
        "matchId": match_id
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.faceit.com/",
        "Cookie":  get_key("faceitcookie")
    }

    res = requests.get(url, params=params, headers=headers)

    if res.status_code != 200:
        log(f"Failed to get download URL for match {match_id}: {res.status_code}")
        return None

    data = res.json()
    return data.get("resource_url")


def download_demo(download_url, filename):
    path = os.path.join(DOWNLOAD_DIR, filename)

    log(f"Downloading: {filename}")

    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    log(f"Saved: {path}")


def get_demos(username, max_matches=5):
    ensure_download_dir()

    log(f"Fetching demos for {username}")

    player_id = get_player_id(username)
    matches = get_match_history(player_id)

    for match in matches[:max_matches]:
        match_id = match["match_id"]

        log(f"Processing match: {match_id}")

        download_url = get_demo_download_url(match_id)

        if not download_url:
            log(f"Skipping match {match_id} (no demo URL)")
            continue

        filename = download_url.split("/")[-1].split("?")[0]

        try:
            download_demo(download_url, filename)
        except Exception as e:
            log(f"Error downloading {filename}: {e}")