from discord.ext import commands
import discord
from datetime import datetime
from database import cursor, conn, save_player_data
from pokemon_api import get_pokemon_data, type_colors
import random

class Breeding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def breed(self, ctx, pokemon1_id: int, pokemon2_id: int):
        await save_player_data(ctx.author.id)
        cursor.execute('SELECT * FROM pokemon WHERE user_id = ? AND id IN (?, ?)', 
                      (str(ctx.author.id), pokemon1_id, pokemon2_id))
        pokemons = cursor.fetchall()
        if len(pokemons) != 2:
            await ctx.send("Kamu harus memilih dua Pokémon yang valid!")
            return

        pokemon1_data = await get_pokemon_data(pokemons[0][2].lower())
        pokemon2_data = await get_pokemon_data(pokemons[1][2].lower())
        if not pokemon1_data or not pokemon2_data:
            await ctx.send("Gagal mendapatkan data Pokémon!")
            return

        if pokemon1_data['types'][0] != pokemon2_data['types'][0]:
            await ctx.send(f"**{pokemons[0][2]}** dan **{pokemons[1][2]}** tidak kompatibel untuk breeding!")
            return

        egg_pokemon = pokemons[0][2].lower()
        is_shiny = 1 if random.randint(1, 4096) == 1 else 0
        hatch_time = int(datetime.now().timestamp()) + 600
        cursor.execute('INSERT INTO eggs (user_id, pokemon_name, hatch_time, is_shiny) VALUES (?, ?, ?, ?)', 
                       (str(ctx.author.id), egg_pokemon, hatch_time, is_shiny))
        conn.commit()

        embed = discord.Embed(
            title="Breeding Berhasil!",
            description=f"**{pokemons[0][2]}** dan **{pokemons[1][2]}** menghasilkan telur **{egg_pokemon.capitalize()}**! "
                        f"Telur akan menetas dalam 10 menit.",
            color=discord.Color.purple()
        )
        embed.set_image(url=(await get_pokemon_data(egg_pokemon))['shiny_sprite' if is_shiny else 'sprite'])
        await ctx.send(embed=embed)

    @commands.command()
    async def hatch(self, ctx):
        await save_player_data(ctx.author.id)
        cursor.execute('SELECT * FROM eggs WHERE user_id = ? AND hatch_time <= ?', 
                       (str(ctx.author.id), int(datetime.now().timestamp())))
        egg = cursor.fetchone()
        if not egg:
            await ctx.send("Kamu tidak punya telur yang siap menetas!")
            return

        pokemon_data = await get_pokemon_data(egg[1])
        if not pokemon_data:
            await ctx.send("Gagal menetas telur!")
            return

        cursor.execute('''
            INSERT INTO pokemon (user_id, name, level, exp, hp, attack, defense, moves, is_shiny)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(ctx.author.id),
            pokemon_data['name'],
            1,
            0,
            pokemon_data['hp'],
            pokemon_data['attack'],
            pokemon_data['defense'],
            ','.join(pokemon_data['moves']),
            egg[3]
        ))
        cursor.execute('DELETE FROM eggs WHERE user_id = ? AND pokemon_name = ?', (str(ctx.author.id), egg[1]))
        conn.commit()

        embed = discord.Embed(
            title="Telur Menetas!",
            description=f"Telurmu menetas menjadi **{pokemon_data['name']}{' ✨' if egg[3] else ''}**!",
            color=type_colors.get(pokemon_data['types'][0], discord.Color.green())
        )
        embed.set_image(url=pokemon_data['shiny_sprite' if egg[3] else 'sprite'])
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Breeding(bot))