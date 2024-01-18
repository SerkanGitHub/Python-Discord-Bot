import discord
from discord.ext import commands, tasks
import datetime
import os
import requests
import json

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

time_in_channel_dict = {}
total_time_in_channels = {}
war_channels = ['TAKIM_1', 'TAKIM_2', 'TAKIM_3']

BEARER_TOKEN_TEST = '8we2wcg70qwszfqwgszoo0vk7e02u4mmoksodcyi'
SHEET_API_ENDPOINT = 'https://sheetdb.io/api/v1/4jpcrb8bvln2k'


@bot.event
async def on_voice_state_update(member, old_state, new_state):
  new_user_channel = new_state.channel
  old_user_channel = old_state.channel

  if old_user_channel and old_user_channel.name in war_channels:
    join_time = time_in_channel_dict.get((member.id, old_user_channel.name))
    if join_time:
      leave_time_utc = datetime.datetime.utcnow()
      time_spent = leave_time_utc - join_time

      total_time_in_channels.setdefault(member.id, datetime.timedelta())
      total_time_in_channels[member.id] += time_spent

      print(
          f"{member.display_name} spent {time_spent} in {old_user_channel.name}"
      )
      time_in_channel_dict[(member.id, old_user_channel.name)] = None

  if new_user_channel and new_user_channel.name in war_channels:
    if old_user_channel and old_user_channel.name in war_channels:
      time_in_channel_dict[(
          member.id, new_user_channel.name)] = datetime.datetime.utcnow()
    else:
      time_in_channel_dict[(
          member.id, new_user_channel.name)] = datetime.datetime.utcnow()


@bot.event
async def on_ready():
  print(f'We have logged in as {bot.user.name}')
  check_voice_channels_loop.start()


@tasks.loop(seconds=5)
async def check_voice_channels_loop():
  current_time = datetime.datetime.utcnow()

  if (current_time - start_time).total_seconds() >= 9:
    print("Bot has run for one hour. Shutting down.")
    await cleanup()


@bot.event
async def on_disconnect():
  await cleanup()


async def cleanup():
  global cleanup_called
  if not cleanup_called:
    cleanup_called = True
    for (member_id, channel_name), join_time in time_in_channel_dict.items():
      if join_time:
        member = discord.utils.get(bot.get_all_members(), id=member_id)
        leave_time_utc = datetime.datetime.utcnow()
        time_spent = leave_time_utc - join_time

        total_time_in_channels.setdefault(member_id, datetime.timedelta())
        total_time_in_channels[member_id] += time_spent

        print(f"{member.display_name} spent {time_spent} in {channel_name}")

    print("\nCumulative Report:")
    print("Member Name | Total Time | Minutes | Seconds")
    print("-" * 45)
    for member_id, time_spent in total_time_in_channels.items():
      if time_spent >= datetime.timedelta(seconds=2):
        member = discord.utils.get(bot.get_all_members(), id=member_id)
        minutes, seconds = divmod(time_spent.total_seconds(), 60)
        print(
            f"{member.display_name} | {time_spent} | {int(minutes)} | {int(seconds)}"
        )
        update_google_sheets(member.display_name)

    await bot.close()


def update_google_sheets(member_name):
  headers = {
      'Authorization': f'Bearer {BEARER_TOKEN_TEST}',
      'Content-Type': 'application/json',
  }

  url = f'{SHEET_API_ENDPOINT}/Member/Papalino'
  search_url = f'{SHEET_API_ENDPOINT}/search_or?Member=Papalino'

  response_search = requests.get(search_url, headers=headers)
  data_search = response_search.json()
  print("#test, data_search ->", data_search)
  
  payload = {
     'data': {
         'Visitor Counter': '9'
     }
 }

  response = requests.patch(url, headers=headers, data=json.dumps(payload))
  data = response.json()

  print(data)

  #https://sheetdb.io/api/v1/58f61be4dda40/search_or?name=Papalino

  # toDo: check the api doc of sheetdb to use & update json format properly


start_time = datetime.datetime.utcnow()
cleanup_called = False

bot.run(os.getenv("TOKEN"))
