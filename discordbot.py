import helpers
from helpers import *
import asyncio
import io
import cs2_inventory_stuff as cs2pc
import discord

import twitch_api
import faceit
from cspromatches import get_matches_from_teams, find_team
from discord.ext import commands, tasks
from get_keys import get_key

from google_calendar_events import add_event

intents = discord.Intents.default()
intents.message_content = True  # required for reading messages
bot = commands.Bot(command_prefix="!", intents=intents)

last_cases_result = "No cached cases value"

is_running = False

discord_channelid_to_ping = 0
userid_to_ping = 0

bot_ideas = read_from_cache("bot_ideas.txt")
bot_bugs = read_from_cache("bot_bugs.txt")

#Twitch related
watched_twitch_channels = {}
watched_twitch_channels_cache = read_from_cache("watched_twitch_channels.txt")
TLMILLISECONDS = 500
twitch_loop_seconds = TLMILLISECONDS/1000
request_returned = True
is_watching = False

bot_try_again_time = 0

cs2_converted_dict = read_from_cache("cs2_converted_dict.txt")
watched_cs2_pro_teams = read_from_cache("watched_cs2_pro_teams.txt")

if(watched_cs2_pro_teams == {}):
    cs2_teams = list()
else:
    cs2_teams = watched_cs2_pro_teams

if("userid_to_ping" in watched_twitch_channels_cache and "discord_channelid_to_ping" in watched_twitch_channels_cache and "channels" in watched_twitch_channels_cache):
    userid_to_ping = watched_twitch_channels_cache["userid_to_ping"]
    discord_channelid_to_ping = watched_twitch_channels_cache["discord_channelid_to_ping"]
    watched_twitch_channels = watched_twitch_channels_cache["channels"]
else:
    watched_twitch_channels_cache = {}
    write_to_cache(watched_twitch_channels_cache, "watched_twitch_channels.txt")

@bot.event
async def on_ready():
    global watched_twitch_channels
    print(f"Logged in as {bot.user}")
    await get_initial_stream_statuses()
    watch_loop.start()
    cache_cs2_items_loop.start()
    cases_loop.start()
    add_cs2_matches_to_calendar.start()

@bot.command()
async def ping(ctx):
    await send_message("Pong!")

@bot.command()
async def cases(ctx):
    global is_running
    is_running = True
    global last_cases_result
    results = await asyncio.to_thread(cs2pc.run_case_price_check)
    cs2pc.write_results_to_file(results)
    last_cases_result = results
    await send_message(results)
    is_running = False

@bot.command()
async def lastCases(ctx):
    print("Writing last cases in chat")
    await send_message(last_cases_result)

@bot.command()
async def inventory_value(ctx):
    global is_running
    is_running = True
    try:
        url = get_args(ctx.message.content)[0].lower()
        response = await asyncio.to_thread(cs2pc.get_inventory_value, url)
        print("returned")
        total_value = response[response.find("Total value"):]
        await send_message(total_value)
        await send_message(response)
    except Exception as e:
        if("429 Client Error" in str(e)):
            await send_message("Rate limited on csfloat. Check logs for reset time")
        else:
            await send_message(str(e))
    is_running = False

@bot.command()
async def inventory(ctx):
    global is_running
    is_running = True

    url = get_args(ctx.message.content)[0]

    final_string = await asyncio.to_thread(cs2pc.get_inventory_no_value, url)
    await send_message(final_string)
    is_running = False

@bot.command()
async def running(ctx):
    global is_running
    if is_running:
        running = "Yes"
    else:
        running = "No"
    await send_message("Is something happening? " + running)

@bot.command()
async def watch(ctx):
    global is_watching
    global channel_to_watch
    global discord_channelid_to_ping
    global userid_to_ping
    global watched_twitch_channels

    channels = get_args(ctx.message.content)

    for channel in channels:
        written_name = twitch_api.get_twitch_username(channel)
        channel_to_watch = written_name.lower()

        if channel_to_watch not in watched_twitch_channels:
            await send_message("Started watching: " + written_name)
            watched_twitch_channels[channel_to_watch] = written_name
            watched_twitch_channels_cache["channels"] = watched_twitch_channels
            write_to_cache(watched_twitch_channels_cache, "watched_twitch_channels.txt")
            is_watching = True
        else:
            await send_message("Stopped watching: " + channel_to_watch)
            watched_twitch_channels.pop(channel_to_watch)
            watched_twitch_channels_cache["channels"] = watched_twitch_channels
            write_to_cache(watched_twitch_channels_cache, "watched_twitch_channels.txt")
            is_watching = len(watched_twitch_channels) > 0

        discord_channelid_to_ping = ctx.channel.id
        userid_to_ping = ctx.author.id

        watched_twitch_channels_cache["userid_to_ping"] = userid_to_ping
        write_to_cache(watched_twitch_channels_cache, "watched_twitch_channels.txt")

        watched_twitch_channels_cache["discord_channelid_to_ping"] = discord_channelid_to_ping
        write_to_cache(watched_twitch_channels_cache, "watched_twitch_channels.txt")

        if(not is_watching):
            watch_loop.stop()
            discord_channelid_to_ping = 0
        else:
            try:
                watch_loop.start()
            except RuntimeError:
                pass

        log("Now watching " + str(watched_twitch_channels.keys()))

@bot.command()
async def ping_me(ctx):
    global discord_channelid_to_ping

    if discord_channelid_to_ping == 0:
        discord_channelid_to_ping = ctx.channel.id

    request_sender = ctx.author.id
    user = await bot.fetch_user(request_sender)

    await send_message(f"Hi {user.mention}")

@bot.command()
async def stop_watching(ctx):
    global watched_twitch_channels
    global is_watching
    global discord_channelid_to_ping
    watched_twitch_channels = {}
    write_to_cache(watched_twitch_channels_cache, "watched_twitch_channels.txt")
    is_watching = False
    message = "Stopped watching all twitch channels"
    log(message)
    await send_message(message)
    discord_channelid_to_ping = 0

@bot.command()
async def watching(ctx):
    global watched_twitch_channels
    output_string = "Currently watching: "
    for channel in watched_twitch_channels:
        output_string += watched_twitch_channels[channel] + ", "
    await send_message(output_string)

@bot.command()
async def set_game(ctx):
    args = get_args(ctx.message.content)

    twitch_api.set_game(args[0], args[1])

@bot.command()
async def get_user_info(ctx):
    user_id = get_args(ctx.message.content)[0]
    user = await bot.fetch_user(user_id)
    await send_message(user.display_name)

@bot.command()
async def dmme(ctx):
    if(ctx.message.author.dm_channel is None):
        channel = await bot.create_dm(await bot.fetch_user(ctx.message.author.id))
    else:
        channel = await bot.fetch_channel(ctx.message.author.dm_channel)
    await send_message("Meow", channel)

@bot.command()
async def dm(ctx):
    args = get_args(ctx.message.content)
    user_id = int(args[0])
    message = args_to_full_string(args)

    user = bot.get_user(user_id)
    if(user is None):
        user = await bot.fetch_user(user_id)
        if(user is None):
            print("DM Failed")

    await user.send(message)

@bot.command()
async def idea(ctx):
    global bot_ideas
    args = get_args(ctx.message.content)
    try:
        my_idea = args[0]
        description = args[1]
    except IndexError:
        return

    if(my_idea == "remove"):
        idea_to_remove = list(bot_ideas.keys())[int(description)]
        bot_ideas.pop(idea_to_remove)
        await send_message(f"Idea {idea_to_remove} removed")
        write_to_cache(bot_ideas, "bot_ideas.txt")
        return

    bot_ideas[my_idea] = args_to_full_string(args)
    write_to_cache(bot_ideas, "bot_ideas.txt")
    await send_message("Idea added")

@bot.command()
async def ideas(ctx):
    global bot_ideas
    idea_string = ""
    count = 0

    if(bot_ideas == {}):
        await send_message("No ideas added")
        return

    for idea in bot_ideas:
        idea_string +=  str(count) + ": " + idea + "\n -" + bot_ideas[idea] + "\n\n"
        count += 1
    await send_message(idea_string)

@bot.command()
async def bug(ctx):
    global bot_bugs
    args = get_args(ctx.message.content)
    try:
        my_bug = args[0]
        description = args[1]
    except IndexError:
        return

    if (my_bug == "remove"):
        bug_to_remove = list(bot_bugs.keys())[int(description)]
        bot_bugs.pop(bug_to_remove)
        await send_message(f"bug {bug_to_remove} removed")
        write_to_cache(bot_bugs, "bot_bugs.txt")
        return

    bot_bugs[my_bug] = args_to_full_string(args)
    write_to_cache(bot_bugs, "bot_bugs.txt")
    await send_message("bug added")

@bot.command()
async def bugs(ctx):
    global bot_bugs
    bug_string = ""
    count = 0

    if (bot_bugs == {}):
        await send_message("No bugs added")
        return

    for bug in bot_bugs:
        bug_string += str(count) + ": " + bug + "\n -" + bot_bugs[bug] + "\n\n"
        count += 1
    await send_message(bug_string)

@bot.command()
async def get_faceit_matches_together(ctx):
    args = get_args(ctx.message.content)
    num_matches = 5
    if(len(args) > 2):
        num_matches = int(args[2])
    await send_message(await faceit.get_matches_together(args[0], args[1], num_matches))
    return

@bot.command()
async def matches(ctx):
    global cs2_teams
    result = await get_matches_from_teams(cs2_teams)
    matches_string = ""
    for team in result:
        if not team:
            continue
        matches_string += f"{team[0]['Team']}\n"
        for match in team:
            matches_string += f"{match['Tournament']}\n{datetime.datetime.fromtimestamp(match['Time']).strftime("%H:%M %d-%m-%Y")} {match['Team']} vs {match['Opponent']}\n\n"

    await send_message(matches_string)

@bot.command()
async def addteams(ctx):
    global cs2_teams
    global cs2_converted_dict
    teams = get_args(ctx.message.content)
    for team in teams:
        if not team in cs2_converted_dict:
            await get_liquipedia_team_name(team)

        if not cs2_converted_dict[team] in cs2_teams:
            cs2_teams.append(cs2_converted_dict[team])
            write_to_cache(cs2_teams, "watched_cs2_pro_teams.txt")
            await send_message("Started watching: " + cs2_converted_dict[team])


@bot.command()
async def removeteam(ctx):
    global cs2_teams
    global cs2_converted_dict

    team = None
    args = get_args(ctx.message.content)
    if not len(args) == 0:
        team = get_args(ctx.message.content)[0]

    if (not team == None) and team in cs2_converted_dict:
        cs2_teams.remove(await get_liquipedia_team_name(team))
        write_to_cache(cs2_teams, "watched_cs2_pro_teams.txt")
        await send_message("Removed " + cs2_converted_dict[team])
    else:
        await send_message("Team not found")

@bot.command()
async def watchedTeams(ctx):
    global cs2_teams

    watched_teams_string = ""

    if cs2_teams != []:
        watched_teams_string += "Watching these teams: "
        for team in cs2_teams:
            last = team == cs2_teams[-1]
            watched_teams_string += str(team)
            if not last:
                watched_teams_string += ", "
    else:
        watched_teams_string += "No teams watched"

    await send_message(watched_teams_string)

@bot.command()
async def add_cs2_to_calendar(ctx):
    teams = get_args(ctx.message.content)
    liquipedia_teams = []
    for team in teams:
        liquipedia_teams.append(await get_liquipedia_team_name(team))
    result = await get_matches_from_teams(liquipedia_teams)
    for team in result:
        for match in team:
            event_name = f'{match['Team']} vs {match['Opponent']}'
            event_description = f'{match['Tournament']}'
            event_time = match['Time']
            add_event(event_name, event_time, event_description)

@tasks.loop(hours=2)
async def cases_loop():
    print("running cases loop")
    global last_cases_result
    last_cases_result = await asyncio.to_thread(cs2pc.run_case_price_check)
    cs2pc.write_results_to_file(last_cases_result)
    print("done running cases loop")

@tasks.loop(seconds=twitch_loop_seconds)
async def watch_loop():
    global request_returned

    if(not request_returned):
        return
    if len(watched_twitch_channels) < 1:
        watch_loop.stop()
    else:
        request_returned = False
        response = await twitch_api.check_for_category_change(watched_twitch_channels)
        if(len(response.keys()) > 0):
            for streamer in response:
                log(streamer + response[streamer], "streamer_logs.txt")
                await ping_category_change(streamer + response[streamer])
        request_returned = True

@tasks.loop(hours=12)
async def add_cs2_matches_to_calendar():
    global cs2_teams
    result = await get_matches_from_teams(cs2_teams)
    for team in result:
        for match in team:
            event_name = f'{match['Team']} vs {match['Opponent']}'
            event_description = f'{match['Tournament']}'
            event_time = match['Time']
            add_event(event_name, event_time, event_description)

@tasks.loop(seconds=30)
async def cache_cs2_items_loop():
    global bot_try_again_time
    if(bot_try_again_time < int(time.time())):
        bot_try_again_time = await asyncio.to_thread(cs2pc.retrieve_price_of_failed_items)

async def get_initial_stream_statuses():
    streamers = twitch_api.get_startup_statuses(watched_twitch_channels)
    streamers_text = ""
    for streamer in streamers:
        written_streamer = twitch_api.get_twitch_username(streamer)
        streamers_text += written_streamer +  streamers[streamer] + "\n"

    await send_message(streamers_text)

def get_args(command):
    args = command.split(" ")
    args.pop(0)
    return args

async def ping_category_change(category):
    global discord_channelid_to_ping
    channel = bot.get_channel(discord_channelid_to_ping)

    message = " " + category
    user = bot.get_user(userid_to_ping)

    if user is None:
        user = await bot.fetch_user(userid_to_ping)

    if channel:
        await send_message(f"{user.mention + message}")

async def send_message(message, channelid = discord_channelid_to_ping):
    global discord_channelid_to_ping
    channel = bot.get_channel(channelid)

    if channel:
        if(len(message) >= 2000):
            file = discord.File(fp=io.BytesIO(message.encode("utf-8")), filename="output.txt")
            await channel.send(file=file)
        else:
            await channel.send(message)

def args_to_full_string(msg):
    string_to_return = ""
    msg.pop(0)
    for arg in msg:
        string_to_return += arg + " "

    return string_to_return

async def get_liquipedia_team_name(team_name):
    global cs2_converted_dict

    if team_name not in cs2_converted_dict:
        liquipedia_team_name = await find_team(team_name)
        print(liquipedia_team_name)
        cs2_converted_dict[team_name] = liquipedia_team_name
        write_to_cache(cs2_converted_dict, "cs2_converted_dict.txt")

    return cs2_converted_dict[team_name]


log_dir_size_bytes = get_dir_size()
log_dir_size_KB = size_bytes_to_next(log_dir_size_bytes)
log_dir_size_MB = size_bytes_to_next(log_dir_size_KB)

cache_dir_size_bytes = get_dir_size(helpers.CACHE_DIR)
cache_dir_size_KB = size_bytes_to_next(cache_dir_size_bytes)
cache_dir_size_MB = size_bytes_to_next(cache_dir_size_KB)

print("Current log size: " + str(log_dir_size_bytes) + " Bytes / " + str(round(log_dir_size_KB, 2)) + " KB / " + str(round(log_dir_size_MB, 2)) + " MB")
print("Current cache size: " + str(cache_dir_size_bytes) + " Bytes / " + str(round(cache_dir_size_KB, 2)) + " KB / " + str(round(cache_dir_size_MB, 2)) + " MB")
bot.run(get_key("discord"))
