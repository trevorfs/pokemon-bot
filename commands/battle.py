from discord.ext import commands
import discord
import asyncio
from database import cursor, conn, exp_for_next_level
from pokemon_api import get_pokemon_data, get_evolution_data, type_effectiveness, type_colors

class Battle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pvp(self, ctx, opponent: discord.Member):
        cursor.execute('SELECT * FROM pokemon WHERE user_id = ?', (str(ctx.author.id),))
        player_pokemon = cursor.fetchone()
        cursor.execute('SELECT * FROM pokemon WHERE user_id = ?', (str(opponent.id),))
        opponent_pokemon = cursor.fetchone()

        if not player_pokemon or not opponent_pokemon:
            await ctx.send("Salah satu pemain tidak memiliki Pokémon!")
            return

        player_data = await get_pokemon_data(player_pokemon[2].lower())
        opponent_data = await get_pokemon_data(opponent_pokemon[2].lower())
        player_data.update({'name': player_pokemon[2], 'hp': player_pokemon[5], 'attack': player_pokemon[6], 
                            'defense': player_pokemon[7], 'is_shiny': player_pokemon[9]})
        opponent_data.update({'name': opponent_pokemon[2], 'hp': opponent_pokemon[5], 'attack': opponent_pokemon[6], 
                              'defense': opponent_pokemon[7], 'is_shiny': opponent_pokemon[9]})

        player_hp = player_data['hp']
        opponent_hp = opponent_data['hp']
        turn = 1
        embed = discord.Embed(title=f"PvP: {player_data['name']} vs {opponent_data['name']}", 
                             color=discord.Color.red())

        while player_hp > 0 and opponent_hp > 0:
            type_multiplier = type_effectiveness.get((player_data['types'][0], opponent_data['types'][0]), 1.0)
            damage = max(1, int((player_data['attack'] - opponent_data['defense'] // 2) * type_multiplier))
            opponent_hp -= damage
            embed.add_field(name=f"Turn {turn}", 
                            value=f"{player_data['name']} menyerang {opponent_data['name']} dengan {damage} damage!", 
                            inline=False)
            
            if opponent_hp <= 0:
                break

            type_multiplier = type_effectiveness.get((opponent_data['types'][0], player_data['types'][0]), 1.0)
            damage = max(1, int((opponent_data['attack'] - player_data['defense'] // 2) * type_multiplier))
            player_hp -= damage
            embed.add_field(name=f"Turn {turn}", 
                            value=f"{opponent_data['name']} menyerang {player_data['name']} dengan {damage} damage!", 
                            inline=False)
            turn += 1
            await asyncio.sleep(1)

        winner = player_data['name'] if opponent_hp <= 0 else opponent_data['name']
        winner_id = str(ctx.author.id) if winner == player_data['name'] else str(opponent.id)
        embed.add_field(name="Hasil", value=f"**{winner}** menang! Pemenang mendapatkan 100 PokéCoins!", inline=False)
        embed.set_footer(text=f"Pertarungan selesai dalam {turn} giliran")
        await ctx.send(embed=embed)

        exp_gain = 100
        cursor.execute('UPDATE players SET credits = credits + 100 WHERE user_id = ?', (winner_id,))
        cursor.execute('UPDATE pokemon SET exp = exp + ? WHERE user_id = ? AND name = ?', 
                       (exp_gain, winner_id, winner))
        conn.commit()

        cursor.execute('SELECT name, level, exp FROM pokemon WHERE user_id = ? AND name = ?', (winner_id, winner))
        pokemon = cursor.fetchone()
        next_level_exp = exp_for_next_level(pokemon[1])
        if pokemon[2] >= next_level_exp:
            cursor.execute('UPDATE pokemon SET level = level + 1, exp = exp - ? WHERE user_id = ? AND name = ?', 
                           (next_level_exp, winner_id, pokemon[0]))
            conn.commit()
            await ctx.send(f"**{pokemon[0]}** naik ke level {pokemon[1] + 1}!")

            evo_data = await get_evolution_data(pokemon[0].lower())
            if evo_data and pokemon[1] + 1 >= evo_data['level']:
                new_name = evo_data['evolves_to'].capitalize()
                cursor.execute('UPDATE pokemon SET name = ? WHERE user_id = ? AND name = ?', 
                               (new_name, winner_id, pokemon[0]))
                conn.commit()
                pokemon_data = await get_pokemon_data(new_name.lower())
                embed = discord.Embed(
                    title="Evolusi!",
                    description=f"Selamat! **{pokemon[0]}** berevolusi menjadi **{new_name}**!",
                    color=type_colors.get(pokemon_data['types'][0], discord.Color.green())
                )
                embed.set_image(url=pokemon_data['sprite'])
                await ctx.send(embed=embed)

    @commands.command()
    async def gym(self, ctx):
        cursor.execute('SELECT badges FROM players WHERE user_id = ?', (str(ctx.author.id),))
        badges = cursor.fetchone()[0]
        if badges >= 8:
            await ctx.send("Kamu sudah mengalahkan semua gym!")
            return

        gym_pokemon = random.choice(['charizard', 'venusaur', 'blastoise'])
        gym_data = await get_pokemon_data(gym_pokemon)
        cursor.execute('SELECT * FROM pokemon WHERE user_id = ?', (str(ctx.author.id),))
        player_pokemon = cursor.fetchone()
        if not player_pokemon:
            await ctx.send("Kamu tidak memiliki Pokémon untuk menantang gym!")
            return

        player_data = await get_pokemon_data(player_pokemon[2].lower())
        player_data.update({'name': player_pokemon[2], 'hp': player_pokemon[5], 'attack': player_pokemon[6], 
                            'defense': player_pokemon[7], 'is_shiny': player_pokemon[9]})

        player_hp = player_data['hp']
        gym_hp = gym_data['hp']
        turn = 1
        embed = discord.Embed(title=f"Gym Battle: {player_data['name']} vs {gym_data['name']}", 
                             color=discord.Color.red())

        while player_hp > 0 and gym_hp > 0:
            type_multiplier = type_effectiveness.get((player_data['types'][0], gym_data['types'][0]), 1.0)
            damage = max(1, int((player_data['attack'] - gym_data['defense'] // 2) * type_multiplier))
            gym_hp -= damage
            embed.add_field(name=f"Turn {turn}", 
                            value=f"{player_data['name']} menyerang {gym_data['name']} dengan {damage} damage!", 
                            inline=False)
            
            if gym_hp <= 0:
                break

            type_multiplier = type_effectiveness.get((gym_data['types'][0], player_data['types'][0]), 1.0)
            damage = max(1, int((gym_data['attack'] - player_data['defense'] // 2) * type_multiplier))
            player_hp -= damage
            embed.add_field(name=f"Turn {turn}", 
                            value=f"{gym_data['name']} menyerang {player_data['name']} dengan {damage} damage!", 
                            inline=False)
            turn += 1
            await asyncio.sleep(1)

        if gym_hp <= 0:
            cursor.execute('UPDATE players SET badges = badges + 1, credits = credits + 200 WHERE user_id = ?', 
                           (str(ctx.author.id),))
            cursor.execute('UPDATE pokemon SET exp = exp + 200 WHERE user_id = ? AND name = ?', 
                           (str(ctx.author.id), player_data['name']))
            conn.commit()
            embed.add_field(name="Hasil", value=f"Kamu mengalahkan gym! Mendapatkan badge ke-{badges + 1} dan 200 PokéCoins!", 
                            inline=False)
            await ctx.send(embed=embed)

            cursor.execute('SELECT name, level, exp FROM pokemon WHERE user_id = ? AND name = ?', 
                           (str(ctx.author.id), player_data['name']))
            pokemon = cursor.fetchone()
            next_level_exp = exp_for_next_level(pokemon[1])
            if pokemon[2] >= next_level_exp:
                cursor.execute('UPDATE pokemon SET level = level + 1, exp = exp - ? WHERE user_id = ? AND name = ?', 
                               (next_level_exp, str(ctx.author.id), pokemon[0]))
                conn.commit()
                await ctx.send(f"**{pokemon[0]}** naik ke level {pokemon[1] + 1}!")

                evo_data = await get_evolution_data(pokemon[0].lower())
                if evo_data and pokemon[1] + 1 >= evo_data['level']:
                    new_name = evo_data['evolves_to'].capitalize()
                    cursor.execute('UPDATE pokemon SET name = ? WHERE user_id = ? AND name = ?', 
                                   (new_name, str(ctx.author.id), pokemon[0]))
                    conn.commit()
                    pokemon_data = await get_pokemon_data(new_name.lower())
                    embed = discord.Embed(
                        title="Evolusi!",
                        description=f"Selamat! **{pokemon[0]}** berevolusi menjadi **{new_name}**!",
                        color=type_colors.get(pokemon_data['types'][0], discord.Color.green())
                    )
                    embed.set_image(url=pokemon_data['sprite'])
                    await ctx.send(embed=embed)
        else:
            embed.add_field(name="Hasil", value=f"Kamu kalah! Coba lagi setelah melatih Pokémonmu!", inline=False)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Battle(bot))