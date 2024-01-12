import discord
from discord.ext import commands, tasks
import datetime
import os
import pytzx

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

time_in_channel_dict = {}  # Dictionary to store join times for each member
war_channels = ['TAKIM_1', 'TAKIM_2', 'TAKIM_3']

@bot.event
async def on_voice_state_update(member, old_state, new_state):
    new_user_channel = new_state.channel
    old_user_channel = old_state.channel

    if old_user_channel and old_user_channel.name in war_channels:
        # Check if the old channel is a war channel
        join_time_utc = time_in_channel_dict.get(member.id, None)
        if join_time_utc:
            leave_time_utc = datetime.datetime.utcnow()
            time_in_channel = (leave_time_utc - join_time_utc).total_seconds()
            print(f"{member.display_name} spent {time_in_channel / 60:.2f} minutes in {old_user_channel.name}")
            time_in_channel_dict[member.id] = datetime.datetime.utcnow()

    if new_user_channel and new_user_channel.name in war_channels:
        # Check if the new channel is a war channel
        time_in_channel_dict[member.id] = datetime.datetime.utcnow()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')

    # Start the loop
    check_voice_channels_loop.start()

@tasks.loop(seconds=5)  # Check every 5 seconds (adjust as needed)
async def check_voice_channels_loop():
    for member_id, join_time_utc in time_in_channel_dict.items():
        member = bot.get_user(member_id)
        if member:
            total_time_in_channels = sum((leave_time_utc - join_time_utc).total_seconds() for leave_time_utc in datetime.datetime.utcnow())
            print(f"{member.display_name} spent {total_time_in_channels / 60:.2f} minutes in total in the war_channels.")
            # Optionally, you can reset the time_in_channel_dict for this member if needed.

bot.run(os.getenv("TOKEN"))
