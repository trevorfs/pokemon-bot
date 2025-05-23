import discord
from discord.ext import commands, tasks
import asyncio
import os


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='p!', intents=intents)


for filename in os.listdir('./commands'):
    if filename.endswith('.py'):
        bot.load_extension(f'commands.{filename[:-3]}')


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    from events.wild_spawn import wild_pokemon_spawn
    wild_pokemon_spawn.start(bot)  

# Jalankan bot
bot.run('') 