from discord.ext import tasks
import discord
import random
from pokemon_api import get_pokemon_data

@tasks.loop(minutes=30)
async def wild_pokemon_spawn(bot):
    channel = bot.get_channel(YOUR_CHANNEL_ID)  # Ganti dengan ID channel
    if not channel:
        return
    pokemon_list = ['pikachu', 'charmander', 'bulbasaur', 'squirtle', 'pidgey', 'eevee', 'jigglypuff']
    wild_pokemon = random.choice(pokemon_list)
    embed = discord.Embed(
        title="Pokémon Liar Muncul!",
        description=f"Seekor **{wild_pokemon.capitalize()}** muncul! Ketik `p!catch {wild_pokemon}` untuk menangkap!",
        color=discord.Color.random()
    )
    pokemon_data = await get_pokemon_data(wild_pokemon)
    embed.set_image(url=pokemon_data['sprite'])
    await channel.send(embed=embed)