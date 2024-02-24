import discord
from discord.ext import commands, tasks
import datetime
import os
import requests
import json

#toDo:
'''
  -> adjust running time to 90 minutes. Start at 7.30 PM on Saturday 27th
  -> consider members that have spent more than 10 minutes in the war_channels
'''

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

time_in_channel_dict = {}
total_time_in_channels = {}
war_channels = ['TAKIM_1', 'TAKIM_2', 'TAKIM_3']

SHEET_API_ENDPOINT = 'https://sheetdb.io/api/v1/4jpcrb8bvln2k'


@bot.event
async def on_voice_state_update(member, old_state, new_state):
  new_user_channel = new_state.channel
  old_user_channel = old_state.channel

  def is_war_channel(channel_name):
    #return any("Go Siege" in channel_name for wc in war_channels)
    return any("Küfürsüz" in channel_name for wc in war_channels)

  if old_user_channel and is_war_channel(old_user_channel.name):
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

  if new_user_channel and is_war_channel(new_user_channel.name):
    if old_user_channel and is_war_channel(old_user_channel.name):
      time_in_channel_dict[(
          member.id, new_user_channel.name)] = datetime.datetime.utcnow()
    else:
      time_in_channel_dict[(
          member.id, new_user_channel.name)] = datetime.datetime.utcnow()


@bot.event
async def on_ready():
  print(f'We have logged in as {bot.user.name}')
  check_voice_channels_loop.start()


@tasks.loop(seconds=600)
async def check_voice_channels_loop():
  current_time = datetime.datetime.utcnow()

  if (current_time - start_time).total_seconds() >= 900:
    print("Bot has run for one hour. Shutting down.")
    print("#test, cleanup on check_voice_channels_loop")
    await cleanup()


@bot.event
async def on_disconnect():
  print("#test, run clean up on disconnect...")
  await cleanup()


async def cleanup():
  global cleanup_called
  if not cleanup_called:
      cleanup_called = True
      print("#test, cleanup_not_called time in channel dict -> ", time_in_channel_dict)

      for (member_id, channel_name), join_time in time_in_channel_dict.items():
          if join_time:
              member = discord.utils.get(bot.get_all_members(), id=member_id)
              if member:  # Check if member is not None
                  leave_time_utc = datetime.datetime.utcnow()
                  time_spent = leave_time_utc - join_time

                  total_time_in_channels.setdefault(member_id, datetime.timedelta())
                  total_time_in_channels[member_id] += time_spent

                  print(f"{member.display_name} spent {time_spent} in {channel_name}")

      print("\nCumulative Report:")
      print("Member Name | Total Time | Minutes | Seconds")
      print("-" * 45)
      print("#test, clean_up_called, time in channel dict -> ", time_in_channel_dict)

      for member_id, time_spent in total_time_in_channels.items():
          if time_spent >= datetime.timedelta(seconds=30):
              member = discord.utils.get(bot.get_all_members(), id=member_id)
              if member:  # Check if member is not None
                  print("#test, clean up called, member spent more than 30 sec, member is -> ", member)
                  minutes, seconds = divmod(time_spent.total_seconds(), 60)
                  print(f"{member.display_name} | {time_spent} | {int(minutes)} | {int(seconds)}")
                  update_google_sheets(member.display_name)

      await bot.close()


def update_google_sheets(member_name_pass):
  # Split the member_name at the first occurrence of "/"
  name_parts = member_name_pass.split('/', 1)

  # Extract the first part of the split (before the first "/")
  member_name = name_parts[0]

  # Now you can use 'first_part' in your subsequent code
  print("Update the sheet for the following member:", member_name)

  headers = {
      'Authorization': f'Bearer {os.getenv("SHEET_GOOGLE_DOCS_TOKEN")}',
      'Content-Type': 'application/json'
  }

  search_url = f'{SHEET_API_ENDPOINT}/search_or?Member={member_name}'
  print("#test, search URL for member -> ", search_url)
  response_search = requests.get(search_url, headers=headers)
  data_search = response_search.json()

  print("#test, response --> ", response_search)
  print("#test, response --> ", data_search)
  if data_search:
    print("#Test, member exists!")
    print("#Test, member is --> ", member_name)
    # Member exists in the sheet
    member_data = data_search[
        0]  # Assuming the first element has the member's data
    url = f'{SHEET_API_ENDPOINT}/Member/{member_name}'

    visitor_counter_str = member_data.get('Visitor Counter', '')

    # Initialize visitor_counter with the existing value
    visitor_counter = int(
        visitor_counter_str) if visitor_counter_str.isdigit() else 0

    if not visitor_counter_str:
      # 'Visitor Counter' is empty, set it to 1
      print("#test, visitor counter is empty, set it to 1!")
      member_data['Visitor Counter'] = '1'
    else:
      # 'Visitor Counter' has a value, increment it by 1
      print("#test, visitor counter has a value, increment it by 1!")
      try:
        visitor_counter += 1
        member_data['Visitor Counter'] = str(visitor_counter)
      except ValueError:
        # Handle the case where 'Visitor Counter' is not a valid integer
        print(
            f"Error: Invalid 'Visitor Counter' value for member {member_name}")

    dates = member_data.get('Dates', [])
    print("#test, dates -->", dates)

    # Check if 'Dates' is a string, if so, convert it to a list
    if isinstance(dates, str):
      dates = [dates]

    # Append the new date in the desired format 'dd.mm.yyyy'
    new_date = datetime.datetime.utcnow().strftime('%d.%m.%Y')
    dates.append(new_date)

    # Convert dates back to a string with the desired format
    member_data['Dates'] = ', '.join(dates)
    print("#test, date format -> ", new_date)

    payload = {
        'data': {
            'Visitor Counter': str(visitor_counter),
            'Dates': dates
        }
    }

    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    data = response.json()

    print(data)
  else:
    # Member does not exist in the sheet, add a new row
    print("#test, member does not exist in the sheet --> ", member_name)
    url = f'{SHEET_API_ENDPOINT}'
    new_date = datetime.datetime.utcnow().strftime('%d.%m.%Y')
    payload = {
        'data': {
            'Member': member_name,
            'Visitor Counter': '1',
            'Dates': new_date
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    data = response.json()


#toDo: replit schedule

start_time = datetime.datetime.utcnow()
cleanup_called = False

bot.run(os.getenv("TOKEN"))
