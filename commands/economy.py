from discord.ext import commands
import discord
from database import cursor, conn, save_player_data

items_data = {
    'pokeball': {'price': 50, 'sell_price': 25, 'description': 'Menangkap Pokémon liar (70% sukses)'},
    'greatball': {'price': 100, 'sell_price': 50, 'description': 'Menangkap Pokémon liar (85% sukses)'},
    'potion': {'price': 100, 'sell_price': 50, 'description': 'Memulihkan 20 HP'},
    'super_potion': {'price': 200, 'sell_price': 100, 'description': 'Memulihkan 50 HP'}
}

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx):
        await save_player_data(ctx.author.id)
        embed = discord.Embed(title="PokéMart", description="Item yang tersedia untuk dibeli:", color=discord.Color.blue())
        for item, data in items_data.items():
            embed.add_field(name=f"{item.capitalize()} ({data['price']} PokéCoins)", 
                            value=data['description'], inline=False)
        embed.add_field(name="Perintah", value="Gunakan `p!buy <item> <jumlah>` untuk membeli!", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx, item_name: str, quantity: int = 1):
        await save_player_data(ctx.author.id)
        item_name = item_name.lower()
        if item_name not in items_data:
            await ctx.send("Item tidak valid! Cek `p!shop` untuk daftar item.")
            return
        if quantity < 1:
            await ctx.send("Jumlah harus lebih dari 0!")
            return

        total_cost = items_data[item_name]['price'] * quantity
        cursor.execute('SELECT credits FROM players WHERE user_id = ?', (str(ctx.author.id),))
        credits = cursor.fetchone()[0]
        if credits < total_cost:
            await ctx.send(f"Kamu tidak punya cukup PokéCoins! Dibutuhkan: {total_cost}, Kamu punya: {credits}")
            return

        cursor.execute('UPDATE players SET credits = credits - ? WHERE user_id = ?', (total_cost, str(ctx.author.id)))
        cursor.execute('INSERT OR REPLACE INTO inventory (user_id, item_name, quantity) VALUES (?, ?, COALESCE((SELECT quantity FROM inventory WHERE user_id = ? AND item_name = ?), 0) + ?)', 
                       (str(ctx.author.id), item_name, str(ctx.author.id), item_name, quantity))
        conn.commit()

        embed = discord.Embed(
            title="Pembelian Berhasil!",
            description=f"Kamu membeli **{quantity} {item_name.capitalize()}** seharga **{total_cost} PokéCoins**!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def sell(self, ctx, item_name: str, quantity: int = 1):
        await save_player_data(ctx.author.id)
        item_name = item_name.lower()
        if item_name not in items_data:
            await ctx.send("Item tidak valid! Cek `p!inventory` untuk daftar item.")
            return
        if quantity < 1:
            await ctx.send("Jumlah harus lebih dari 0!")
            return

        cursor.execute('SELECT quantity FROM inventory WHERE user_id = ? AND item_name = ?', 
                       (str(ctx.author.id), item_name))
        item = cursor.fetchone()
        if not item or item[0] < quantity:
            await ctx.send(f"Kamu tidak punya cukup **{item_name.capitalize()}** untuk dijual!")
            return

        total_credits = items_data[item_name]['sell_price'] * quantity
        cursor.execute('UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND item_name = ?', 
                       (quantity, str(ctx.author.id), item_name))
        cursor.execute('UPDATE players SET credits = credits + ? WHERE user_id = ?', 
                       (total_credits, str(ctx.author.id)))
        conn.commit()

        embed = discord.Embed(
            title="Penjualan Berhasil!",
            description=f"Kamu menjual **{quantity} {item_name.capitalize()}** dan mendapatkan **{total_credits} PokéCoins**!",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def inventory(self, ctx):
        await save_player_data(ctx.author.id)
        cursor.execute('SELECT item_name, quantity FROM inventory WHERE user_id = ?', (str(ctx.author.id),))
        items = cursor.fetchall()
        cursor.execute('SELECT credits FROM players WHERE user_id = ?', (str(ctx.author.id),))
        credits = cursor.fetchone()[0]

        embed = discord.Embed(title=f"Inventory {ctx.author.name}", color=discord.Color.blue())
        embed.add_field(name="PokéCoins", value=f"{credits} PokéCoins", inline=False)
        if not items:
            embed.add_field(name="Item", value="Inventory kosong!", inline=False)
        else:
            for item_name, quantity in items:
                if quantity > 0:
                    embed.add_field(name=item_name.capitalize(), value=f"Jumlah: {quantity}", inline=True)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Economy(bot))