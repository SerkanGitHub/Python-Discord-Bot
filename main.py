import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import os
import pytz

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

time_in_channel_dict = {}  # Dictionary to store join times for each member

@bot.event
async def on_voice_state_update(member, old_state, new_state):
    new_user_channel = new_state.channel
    old_user_channel = old_state.channel

    print(f"Member: {member.display_name}")
    print(f"Old Channel: {old_user_channel.name if old_user_channel else 'None'}")
    print(f"New Channel: {new_user_channel.name if new_user_channel else 'None'}")

    if old_user_channel is None and new_user_channel is not None:
        # User Join a voice channel
        time_in_channel_dict[member.id] = datetime.datetime.utcnow()
    elif old_user_channel is not None and new_user_channel is None:
        # User Leave a voice channel
        join_time_utc = time_in_channel_dict.get(member.id, None)
        if join_time_utc:
            leave_time_utc = datetime.datetime.utcnow()
            time_in_channel = (leave_time_utc - join_time_utc).total_seconds()
            print(f"{member.display_name} spent {time_in_channel / 60:.2f} minutes in {old_user_channel.name}")
    elif old_user_channel is not None and new_user_channel is not None and old_user_channel.id != new_user_channel.id:
      # User Switch a voice channel
      join_time_utc = time_in_channel_dict.get(member.id, None)
      if join_time_utc:
          leave_time_utc = datetime.datetime.utcnow()
          time_in_channel = (leave_time_utc - join_time_utc).total_seconds()
          print(f"{member.display_name} spent {time_in_channel / 60:.2f} minutes in {old_user_channel.name}")
      time_in_channel_dict[member.id] = datetime.datetime.utcnow()
      
async def check_voice_channels(guild, war_channel_names, stats_channel,
                               time_threshold, start_date, end_date,
                               start_hour, end_hour):
    now = datetime.datetime.now(pytz.timezone('Europe/Berlin'))
    current_time_utc = datetime.datetime.utcnow()

    if start_date <= now <= end_date and now.weekday() in [0, 1] and start_hour <= now.hour < end_hour:
        print("#test, #test, #test")
        result_table = []

        for channel_name in war_channel_names:
            voice_channel = discord.utils.get(guild.voice_channels, name=channel_name)

            if voice_channel:
                for member_id, state in voice_channel.voice_states.items():
                    member = guild.get_member(member_id)
                    print("#test, member is -> ", member)

        if result_table:
            print("#test, result_table TRUE -> ", result_table)
            result_message = "\n".join(result_table)
            war_channel = discord.utils.get(guild.channels, name=stats_channel)
            print("#test, war channel -> ", war_channel)
            if war_channel:
                await war_channel.send(
                    f"Members in voice channels for at least {time_threshold / 60:.2f} minutes:\n"
                    + result_message)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')

    # Start the loop
    check_voice_channels_loop.start()

@tasks.loop(seconds=5)  # Check every 5 seconds (adjust as needed)
async def check_voice_channels_loop():
      guild_id = 933806488823136276  # Replace with your server ID
      guild = bot.get_guild(guild_id)
      war_channel_names = ['TAKIM_1', 'TAKIM_2', 'TAKIM_3']
      stats_channel = 'stats'
      time_threshold = 60  # 1800 = 30 minutes, 60 = 1 minute, etc.
      berlin_timezone = pytz.timezone('Europe/Berlin')
      start_date = berlin_timezone.localize(datetime.datetime(2024, 1, 1))
      end_date = berlin_timezone.localize(datetime.datetime(2024, 3, 1))
      start_hour = 2  # 2 pm
      end_hour = 3  # 3 pm

      await check_voice_channels(guild, war_channel_names, stats_channel,
                                 time_threshold, start_date, end_date, start_hour,
                                 end_hour)

bot.run(os.getenv("TOKEN"))
