from discord.ext import commands
import discord
from database import cursor, conn, save_player_data, exp_for_next_level
from pokemon_api import get_pokemon_data, type_colors

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def start(self, ctx):
        await save_player_data(ctx.author.id)
        cursor.execute('SELECT * FROM pokemon WHERE user_id = ?', (str(ctx.author.id),))
        if cursor.fetchone():
            await ctx.send("Kamu sudah memulai petualangan Pokémon!")
            return

        embed = discord.Embed(
            title="Pilih Starter Pokémon!",
            description="Ketik `p!pick <nama>` untuk memilih: **Pikachu**, **Charmander**, **Bulbasaur**, **Squirtle**, **Eevee**.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def pick(self, ctx, pokemon_name: str):
        await save_player_data(ctx.author.id)
        pokemon_name = pokemon_name.lower()
        valid_starters = ['pikachu', 'charmander', 'bulbasaur', 'squirtle', 'eevee']
        if pokemon_name not in valid_starters:
            await ctx.send("Pokémon tidak valid! Pilih: Pikachu, Charmander, Bulbasaur, Squirtle, atau Eevee.")
            return

        cursor.execute('SELECT * FROM pokemon WHERE user_id = ?', (str(ctx.author.id),))
        if cursor.fetchone():
            await ctx.send("Kamu sudah punya starter Pokémon!")
            return

        pokemon_data = await get_pokemon_data(pokemon_name)
        if not pokemon_data:
            await ctx.send("Gagal mengambil data Pokémon!")
            return

        is_shiny = 1 if random.randint(1, 4096) == 1 else 0
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
            is_shiny
        ))
        conn.commit()

        embed = discord.Embed(
            title="Starter Pokémon Dipilih!",
            description=f"Kamu memilih **{pokemon_data['name']}{' ✨' if is_shiny else ''}** sebagai starter Pokémon!",
            color=type_colors.get(pokemon_data['types'][0], discord.Color.blue())
        )
        embed.set_image(url=pokemon_data['shiny_sprite' if is_shiny else 'sprite'])
        await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx):
        await save_player_data(ctx.author.id)
        cursor.execute('SELECT * FROM pokemon WHERE user_id = ?', (str(ctx.author.id),))
        pokemons = cursor.fetchall()
        if not pokemons:
            await ctx.send("Kamu belum memiliki Pokémon!")
            return

        embed = discord.Embed(title=f"Pokémon milik {ctx.author.name}", color=discord.Color.gold())
        for pokemon in pokemons:
            pokemon_data = await get_pokemon_data(pokemon[2].lower())
            embed.add_field(
                name=f"{pokemon[2]}{' ✨' if pokemon[9] else ''} (Level {pokemon[3]})",
                value=f"HP: {pokemon[5]} | Attack: {pokemon[6]} | Defense: {pokemon[7]}\n"
                      f"Moves: {pokemon[8]}\nEXP: {pokemon[4]}/{exp_for_next_level(pokemon[3])}",
                inline=False
            )
            embed.color = type_colors.get(pokemon_data['types'][0], discord.Color.gold())
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Basic(bot))