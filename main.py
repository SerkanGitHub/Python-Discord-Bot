import discord
from discord.ext import commands, tasks
import datetime
import os

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

time_in_channel_dict = {}  # Dictionary to store join times for each member and channel
total_time_in_channels = {}  # Dictionary to store total time spent by each member in all channels
war_channels = ['TAKIM_1', 'TAKIM_2', 'TAKIM_3']

@bot.event
async def on_voice_state_update(member, old_state, new_state):
    new_user_channel = new_state.channel
    old_user_channel = old_state.channel

    if old_user_channel and old_user_channel.name in war_channels:
        # Check if the old channel is a war channel
        join_time = time_in_channel_dict.get((member.id, old_user_channel.name))
        if join_time:
            leave_time_utc = datetime.datetime.utcnow()
            time_spent = leave_time_utc - join_time  # Use the recorded join time

            # Accumulate time spent in all channels
            total_time_in_channels.setdefault(member.id, datetime.timedelta())
            total_time_in_channels[member.id] += time_spent

            print(f"{member.display_name} spent {time_spent} in {old_user_channel.name}")
            time_in_channel_dict[(member.id, old_user_channel.name)] = None  # Reset join time

    if new_user_channel and new_user_channel.name in war_channels:
        # Check if the new channel is a war channel
        if old_user_channel and old_user_channel.name in war_channels:
            time_in_channel_dict[(member.id, new_user_channel.name)] = datetime.datetime.utcnow()
        else:
            # If coming from a non-war channel to a war channel, set the join time
            time_in_channel_dict[(member.id, new_user_channel.name)] = datetime.datetime.utcnow()

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
    global cleanup_called
    if not cleanup_called:
        cleanup_called = True
        # Check the last known state for members still in war channels
        for (member_id, channel_name), join_time in time_in_channel_dict.items():
            if join_time:
                member = discord.utils.get(bot.get_all_members(), id=member_id)
                # Calculate the time spent in the last channel
                leave_time_utc = datetime.datetime.utcnow()
                time_spent = leave_time_utc - join_time

                # Accumulate time spent in all channels
                total_time_in_channels.setdefault(member_id, datetime.timedelta())
                total_time_in_channels[member_id] += time_spent

                print(f"{member.display_name} spent {time_spent} in {channel_name}")

        # Print the table to the console
        print("\nCumulative Report:")
        print("Member Name | Total Time | Minutes | Seconds")
        print("-" * 45)
        for member_id, time_spent in total_time_in_channels.items():
            member = discord.utils.get(bot.get_all_members(), id=member_id)
            minutes, seconds = divmod(time_spent.total_seconds(), 60)
            print(f"{member.display_name} | {time_spent} | {int(minutes)} | {int(seconds)}")

        await bot.close()

# Set the start time
start_time = datetime.datetime.utcnow()
cleanup_called = False

# Run the bot
bot.run(os.getenv("TOKEN"))
