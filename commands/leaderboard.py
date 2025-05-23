from discord.ext import commands
import discord
from database import cursor, save_player_data

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def leaderboard(self, ctx):
        await save_player_data(ctx.author.id)
        cursor.execute('SELECT user_id, COUNT(*) as count FROM pokemon GROUP BY user_id ORDER BY count DESC LIMIT 5')
        leaders = cursor.fetchall()
        embed = discord.Embed(title="Leaderboard Pokémon", color=discord.Color.gold())
        for i, (user_id, count) in enumerate(leaders, 1):
            user = await self.bot.fetch_user(int(user_id))
            embed.add_field(name=f"{i}. {user.name}", value=f"Pokémon: {count}", inline=False)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Leaderboard(bot))