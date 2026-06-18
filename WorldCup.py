import pandas as pd
import time

from get_keys import get_key
import requests

google_to_tyler = {
    "Bosnia and Herzegovina": "Bosnia",
    "Czechia":"Czechia",
    "Paraguay":"Paraguay",
    "Switzerland":"Switzerland",
    "Morocco":"Morocco",
    "Scotland":"Scotland",
    "Türkiye":"Turkiye",
    "Curaçao":"Curacao",
    "Japan":"Japan",
    "Ecuador":"Ecuador",
    "Tunisia":"Tunisia",
    "Cape Verde":"Cape Verde",
    "Egypt":"Egypt",
    "Uruguay":"Uruguay",
    "New Zealand":"New Zealand",
    "Senegal":"Senegal",
    "Norway":"Norway",
    "Algeria":"Algeria",
    "Jordan":"Jordan",
    "DR Congo":"DR Congo",
    "Croatia":"Croatia",
    "Panama":"Panama",
    "Colombia":"Colombia",
    "South Africa":"South Africa",
    "Qatar":"Qatar",
    "South Korea":"South Korea",
    "Australia":"Australia",
    "Haiti":"Haiti",
    "Sweden":"Sweden",
    "Ivory Coast":"Ivory Coast",
    "Saudi Arabia":"Saudi Arabia",
    "Iran":"Iran",
    "Austria":"Austria",
    "Iraq":"Iraq",
    "Uzbekistan":"Uzbekistan",
    "Ghana":"Ghana",
    "Canada":"Canada",
    "Brazil":"Brazil",
    "Mexico":"Mexico",
    "Germany":"Germany",
    "Netherlands":"Netherlands",
    "USA":"United States",
    "France":"France",
    "Spain":"Spain",
    "Belgium":"Belgium",
    "England":"England",
    "Portugal":"Portugal",
    "Argentina":"Argentina"
}

SECRET_KEY = get_key('SerpApi')

params = {
    "engine": "google",
    "q": "FIFA World Cup 2026 matches results",
    "api_key": SECRET_KEY
}

response = requests.get(
    "https://serpapi.com/search",
    params=params
)


data = response.json()

games = data["sports_results"]["games"]

def get_winner(game):
    if game["teams"][0]["score"] > game["teams"][1]["score"]:
        return google_to_tyler[game["teams"][0]["name"]]
    elif game["teams"][0]["score"] < game["teams"][1]["score"]:
        return google_to_tyler[game["teams"][1]["name"]]
    else:
        return "Draw"

df = pd.read_excel("2026 FIFA World Cup Pool.xlsx")

DATE_COL = "DATE"
T1_COL = "MATCHUP"
T2_COL = "Unnamed: 5"

entry = False

matches = {}
predictions_per_match = {}

rows = []
columns = []
columns_ref = {}

col_count = 0
for column in df.columns:
    if col_count >= 24:
        break
    columns_ref[col_count] = column
    columns.append(column)
    col_count += 1

def build_match_order():
    global match_order
    global df

    for column in df.columns:
        if column == "MATCH":
            df[column].astype("Int64")
            for match in df[column].values:
                try:
                    guesses_dict[int(match)] = {}
                    match_order.append(int(match))
                except ValueError:
                    pass

correct_guesses_by_player = {}

def get_guesses():
    global guesses_dict
    global players
    global df
    global correct_guesses_by_player

    entry = False
    for column in df.columns:
        if (column == "Tyler"):
            entry = True
        if entry:
            players.append(column)
            correct_guesses_by_player[column] = 0
            winners_processed = 0
            for winner in df[column].values:
                if winners_processed == 72:
                    break
                guesses_dict[match_order[winners_processed]][column] = winner
                winners_processed += 1
        if (column == "Daniel"):
            break

match_dict = {}
def build_match_dict():
    global df
    global match_dict

    for i in range(len(match_order)):
        match_dict[match_order[i]] = {"T1": df[T1_COL][i],"T2": df[T2_COL][i], "Group": df["GROUP"][i]}

def get_match_number(api_match):
    t1 = api_match["teams"][0]["name"]
    t2 = api_match["teams"][1]["name"]
    for match in match_dict:
        if (match_dict[match]["T1"] == google_to_tyler[t1] and match_dict[match]["T2"] == google_to_tyler[t2]) or (match_dict[match]["T1"] == google_to_tyler[t2] and match_dict[match]["T2"] == google_to_tyler[t1]):
            return match

    return None


match_order = []
players = []
guesses_dict = {}

build_match_order()
get_guesses()
build_match_dict()

for match in games:
    winner = get_winner(match)
    for player in players:
        match_number = get_match_number(match)
        player_guess = guesses_dict[match_number][player]
        if winner == player_guess:
            correct_guesses_by_player[player] += 1

summary = "Current standings:\n"

for player in correct_guesses_by_player:
    summary += player + ": " + str(correct_guesses_by_player[player]) + f" ({round((100*correct_guesses_by_player[player]/len(games)), 2)}%)"+ "\n"

with open(f"correct_guesses_output\\guesses_output_{time.time()}.txt", "w") as f:
    f.writelines(summary)

