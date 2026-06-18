from playwright.async_api import async_playwright
import time

from helpers import log

BASE_URL = "https://liquipedia.net/counterstrike/"

async def get_matches_from_teams(teams):
    full_content = []
    matchups = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        for team in teams:
            page_url = BASE_URL + team
            await page.goto(page_url)
            await page.wait_for_load_state("load")
            try:
                carousel = page.locator("div.fo-nttax-infobox-container .carousel-content")
                await page.wait_for_selector(".carousel-item", timeout=2000)
                matches = carousel.locator(".carousel-item")
                count = await matches.count()
                team_match_list = []
                for i in range(count):
                    match = matches.nth(i)
                    match_time = await get_match_time(match)
                    tournament = (await get_tournament(match)).replace('/', " ")
                    requested_team, opponent_team = await get_teams(match)
                    match_found = False
                    if opponent_team in matchups:
                        for match in matchups[opponent_team]:
                            match_found = match["Opponent"] == requested_team and match["Time"] == match_time
                            
                            if match_found:
                                break

                    if match_time > int(time.time()) and not match_found:
                        team_match_list.append({"Time": match_time, "Tournament": tournament, "Team": requested_team, "Opponent": opponent_team})
                        if not requested_team in matchups:
                            matchups[requested_team] = []
                        matchups[requested_team].append({"Opponent": opponent_team, "Time": match_time})
                full_content.append(team_match_list)
            except:
                log(f"No matches found for {team}")
                pass

        await browser.close()
    return full_content

async def get_match_time(match):
    match_time_span = match.locator(".match-info-countdown span.timer-object")
    return int(await match_time_span.get_attribute("data-timestamp"))

async def get_tournament(match):
    return await match.locator(".match-info-tournament-name a").get_attribute("title")

async def get_teams(match):
    row = match.locator(".match-info-opponent-row").nth(0)
    link = row.locator(".name a").first

    requested_team = await link.inner_text()

    row = match.locator(".match-info-opponent-row").nth(1)
    link = row.locator(".name a").first

    opponent_team = await link.inner_text()

    return requested_team, opponent_team

async def find_team(searched_team):
    page_url = BASE_URL + "Main_Page"
    prefixes_list = ["", "team_", "team:"]
    results_list = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(page_url)
        await page.wait_for_load_state("load")
        for prefix in prefixes_list:
            result, is_team_name = await perform_search(page, prefix + searched_team)
            if not result is None and not is_team_name:
                teams_results = await eliminate_search_results_and_get_links(result)
                for team_link in teams_results:
                    if team_link not in results_list:
                        results_list.append(team_link)
            if(is_team_name):
                await browser.close()
                return result

        t1_name = await get_tier_1_team_name(page, results_list)
        await browser.close()
        return t1_name

async def perform_search(page, search_input):
    await page.fill("#searchInput", search_input)
    await page.click(".main-nav__search-button")
    await page.wait_for_load_state("load")
    if "index.php?search=" in page.url:
        try:
            await page.wait_for_selector(".mw-search-result-heading", timeout=2000)
            return page.locator(".mw-search-result-heading"), False
        except:
            return None, False
    else:
        if (await is_team_page(page)):
            team_name = page.url.split("/")[-1]
            return team_name, True
        else:
            return None, False


async def eliminate_search_results_and_get_links(results):
    results_list = []
    count = min(5,await results.count())
    for i in range(count):
        results_list.append(results.nth(i))
    teams_results = []
    for result in results_list:
        if "(category Teams using TeamCardImage)" in await result.inner_text():
            a = result.locator(":scope > a")
            link = await a.get_attribute("href")
            teams_results.append(link)
    if(len(teams_results) == 0):
        for result in results_list:
            a = result.locator(":scope > a")
            link = await a.get_attribute("href")
            teams_results.append(link)

    return teams_results

async def get_tier_1_team_name(page, teams_results):
    max_count = -1
    max_count_team_name = ""
    for team_url in teams_results:
        team_name = team_url.split("/")[-1]
        await page.goto(BASE_URL + team_name)
        await page.wait_for_load_state("load")
        locator = page.get_by_text("S-Tier")
        count = await locator.count()
        print(team_name + " " + str(count))
        if count > max_count:
            max_count = count
            max_count_team_name = team_name
    return max_count_team_name

async def is_team_page(page):
    locator = page.get_by_text("Player Roster")
    return (await locator.count()) > 0