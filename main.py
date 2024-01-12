import discord
from discord.ext import commands, tasks
import datetime
import os
import pytz
import asyncio

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

time_in_channel_dict = {}  # Dictionary to store join times for each member
total_time_in_channels = {}  # Dictionary to store total time spent by each member in each channel
war_channels = ['TAKIM_1', 'TAKIM_2', 'TAKIM_3']

@bot.event
async def on_voice_state_update(member, old_state, new_state):
    new_user_channel = new_state.channel
    old_user_channel = old_state.channel

    if old_user_channel and old_user_channel.name in war_channels:
        # Check if the old channel is a war channel
        join_time_utc = time_in_channel_dict.get((member.id, old_user_channel.name), None)
        if join_time_utc:
            leave_time_utc = datetime.datetime.utcnow()
            time_spent = leave_time_utc - join_time_utc

            # Accumulate time spent in the channel
            total_time_in_channels.setdefault(member.id, {}).setdefault(old_user_channel.name, datetime.timedelta())
            total_time_in_channels[member.id][old_user_channel.name] += time_spent

            print(f"{member.display_name} spent {time_spent} in {old_user_channel.name}")
            time_in_channel_dict[(member.id, old_user_channel.name)] = None  # Reset join time

    if new_user_channel and new_user_channel.name in war_channels:
        # Check if the new channel is a war channel
        time_in_channel_dict[(member.id, new_user_channel.name)] = datetime.datetime.utcnow()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')

    # Start the loop
    check_voice_channels_loop.start()

@tasks.loop(seconds=5)  # Check every 5 seconds (adjust as needed)
async def check_voice_channels_loop():
    for member_id, channels in total_time_in_channels.items():
        for channel_name, time_spent in channels.items():
            minutes, seconds = divmod(time_spent.total_seconds(), 60)
            print(f"Member {member_id} spent {int(minutes)} minutes and {int(seconds)} seconds in {channel_name}")

# Run the bot
bot.run(os.getenv("TOKEN"))
