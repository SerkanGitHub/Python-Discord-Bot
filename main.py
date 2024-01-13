import discord
from discord.ext import commands, tasks
import datetime
import os
import asyncio

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

time_in_channel_dict = {}  # Dictionary to store join times for each member and channel
total_time_in_channels = {}  # Dictionary to store total time spent by each member in each channel
war_channels = ['TAKIM_1', 'TAKIM_2', 'TAKIM_3']

@bot.event
async def on_voice_state_update(member, old_state, new_state):
    new_user_channel = new_state.channel
    old_user_channel = old_state.channel

    if old_user_channel and old_user_channel.name in war_channels:
        # Check if the old channel is a war channel
        join_times = time_in_channel_dict.get((member.id, old_user_channel.name), [])
        if join_times:
            leave_time_utc = datetime.datetime.utcnow()
            time_spent = leave_time_utc - join_times[-1]  # Use the last recorded join time

            # Accumulate time spent in the channel
            total_time_in_channels.setdefault(member.id, {}).setdefault(old_user_channel.name, datetime.timedelta())
            total_time_in_channels[member.id][old_user_channel.name] += time_spent

            print(f"{member.display_name} spent {time_spent} in {old_user_channel.name}")
            time_in_channel_dict[(member.id, old_user_channel.name)].append(leave_time_utc)  # Add the new leave time

    if new_user_channel and new_user_channel.name in war_channels:
        # Check if the new channel is a war channel
        time_in_channel_dict.setdefault((member.id, new_user_channel.name), []).append(datetime.datetime.utcnow())

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')

    # Start the loop
    check_voice_channels_loop.start()

@tasks.loop(seconds=5)  # Check every 5 seconds (adjust as needed)
async def check_voice_channels_loop():
    current_time = datetime.datetime.utcnow()

    # Check if an hour has passed
    if (current_time - start_time).total_seconds() >= 30:
        print("Bot has run for one hour. Shutting down.")
        await cleanup()

@bot.event
async def on_disconnect():
    await cleanup()

async def cleanup():
    # Check the last known state for members still in war channels
    for (member_id, channel_name), join_times in time_in_channel_dict.items():
        if join_times:
            # Calculate the time spent in the last channel
            leave_time_utc = datetime.datetime.utcnow()
            time_spent = leave_time_utc - join_times[-1]

            # Accumulate time spent in the channel
            total_time_in_channels.setdefault(member_id, {}).setdefault(channel_name, datetime.timedelta())
            total_time_in_channels[member_id][channel_name] += time_spent

            print(f"{member_id} spent {time_spent} in {channel_name}")

    # Create a report or table with cumulative data
    report = "Cumulative Time Report:\n"
    for member_id, channels in total_time_in_channels.items():
        report += f"\nMember {member_id}:\n"
        for channel_name, time_spent in channels.items():
            minutes, seconds = divmod(time_spent.total_seconds(), 60)
            report += f"  {channel_name}: {int(minutes)} minutes and {int(seconds)} seconds\n"

    # Get the "stats" channel
    stats_channel = discord.utils.get(bot.get_all_channels(), name='stats')

    # Send the report to the "stats" channel
    if stats_channel:
        await stats_channel.send(report)
    else:
        print("Stats channel not found.")

    await bot.close()

# Set the start time
start_time = datetime.datetime.utcnow()

# Run the bot
bot.run(os.getenv("TOKEN"))
