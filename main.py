import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import os

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

async def check_voice_channels(guild, war_channel_names, time_threshold, start_date, end_date, start_hour, end_hour):
    now = datetime.datetime.utcnow()
    current_time = now.replace(tzinfo=datetime.timezone.utc)  # Make current_time UTC-aware

    if start_date <= now <= end_date and now.weekday() in [1, 5] and start_hour <= now.hour < end_hour:
        result_table = []

        for channel_name in war_channel_names:
            voice_channel = discord.utils.get(guild.voice_channels, name=channel_name)

            if voice_channel:
                for member in voice_channel.members:
                    if member.voice and member.voice.channel:
                        join_time = member.joined_at
                        if join_time is not None:
                            time_in_channel = (current_time - join_time).total_seconds()
                            if time_in_channel >= time_threshold:
                                result_table.append(f"{member.display_name} - {time_in_channel / 60:.2f} minutes in {voice_channel.name}")

        if result_table:
            result_message = "\n".join(result_table)
            war_channel = discord.utils.get(guild.channels, name=war_channel_names[0])  # Assuming the first WAR channel is used for the result
            await war_channel.send(f"Members in voice channels for at least {time_threshold / 60:.2f} minutes:\n" + result_message)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')
    guild_id = 933806488823136276  # Replace with your server ID
    guild = bot.get_guild(guild_id)

    war_channel_names = ['TAKIM_1', 'TAKIM_2', 'TAKIM_3']
    time_threshold = 1800  # 30 minutes
    start_date = datetime.datetime(2024, 1, 1)
    end_date = datetime.datetime(2024, 3, 1)
    start_hour = 20  # 8 pm
    end_hour = 21  # 9 pm

    await check_voice_channels(guild, war_channel_names, time_threshold, start_date, end_date, start_hour, end_hour)

    # Start the loop
    check_voice_channels_loop.start(guild, war_channel_names, time_threshold, start_date, end_date, start_hour, end_hour)

@tasks.loop(seconds=60)  # Check every 60 seconds (adjust as needed)
async def check_voice_channels_loop(guild, war_channel_names, time_threshold, start_date, end_date, start_hour, end_hour):
    await check_voice_channels(guild, war_channel_names, time_threshold, start_date, end_date, start_hour, end_hour)

bot.run(os.getenv("TOKEN"))
