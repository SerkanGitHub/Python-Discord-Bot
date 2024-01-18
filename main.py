import discord
from discord.ext import commands, tasks
import datetime
import os
import requests
import re

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

  current_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")

  response = requests.get(SHEET_API_ENDPOINT, headers=headers)
  data = response.json()

  if response.status_code == 200:
    member_name_lower = member_name.lower()
    member_exists = any(row['Member'].lower() == member_name_lower
                        for row in data)

    if member_exists:
      updated_data = [{
          'Visitor Counter':
          str(int(row.get('Visitor Counter', 0) or 0) + 1),
          'Dates':
          current_date
          if not row.get('Dates') else f"{row['Dates']},{current_date}",
      } if row['Member'].lower() == member_name_lower else row for row in data]

      row_id = next(
          (row.get('id')
           for row in data if row['Member'].lower() == member_name_lower),
          None)

      if row_id:
        update_url = f'{SHEET_API_ENDPOINT}/{row_id}'
        response = requests.patch(update_url,
                                  headers=headers,
                                  json=updated_data[0])

        if response.status_code == 200:
          print(f"Updated Google Sheets for existing member: {member_name}")
        else:
          print(
              f"Failed to update Google Sheets for existing member: {member_name}"
          )
          print("Status Code:", response.status_code)
      else:
        print(f"Row ID not found for existing member: {member_name}")
    else:
      new_row = {
          'Member': member_name,
          'Visitor Counter': 1,
          'Dates': [current_date],
      }

      response = requests.post(SHEET_API_ENDPOINT,
                               headers=headers,
                               json=new_row)

      if response.status_code == 201:
        print(f"Added new row to Google Sheets for new member: {member_name}")
      else:
        print(
            f"Failed to add new row to Google Sheets for new member: {member_name}"
        )
        print("Status Code:", response.status_code)
  else:
    print(f"Failed to fetch data from Google Sheets: {response.status_code}")


start_time = datetime.datetime.utcnow()
cleanup_called = False

bot.run(os.getenv("TOKEN"))
