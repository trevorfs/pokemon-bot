import aiohttp
import discord

# Warna berdasarkan tipe Pokémon
type_colors = {
    'fire': discord.Color.red(),
    'water': discord.Color.blue(),
    'grass': discord.Color.green(),
    'electric': discord.Color.gold(),
    'normal': discord.Color.light_grey(),
}

# Pengali tipe untuk PvP
type_effectiveness = {
    ('fire', 'grass'): 2.0, ('fire', 'water'): 0.5,
    ('water', 'fire'): 2.0, ('water', 'grass'): 0.5,
    ('grass', 'water'): 2.0, ('grass', 'fire'): 0.5,
    ('electric', 'water'): 2.0, ('electric', 'grass'): 0.5,
}

async def get_pokemon_data(name):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://pokeapi.co/api/v2/pokemon/{name.lower()}') as response:
            if response.status == 200:
                data = await response.json()
                types = [t['type']['name'] for t in data['types']]
                return {
                    'name': data['name'].capitalize(),
                    'hp': data['stats'][0]['base_stat'],
                    'attack': data['stats'][1]['base_stat'],
                    'defense': data['stats'][2]['base_stat'],
                    'moves': [move['move']['name'] for move in data['moves'][:4]],
                    'types': types,
                    'sprite': data['sprites']['front_default'],
                    'shiny_sprite': data['sprites']['front_shiny']
                }
            return None

async def get_evolution_data(name):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://pokeapi.co/api/v2/pokemon-species/{name.lower()}') as response:
            if response.status == 200:
                data = await response.json()
                async with session.get(data['evolution_chain']['url']) as evo_response:
                    evo_data = await evo_response.json()
                    chain = evo_data['chain']
                    if chain['species']['name'] == name.lower() and chain['evolves_to']:
                        return {'evolves_to': chain['evolves_to'][0]['species']['name'], 
                                'level': chain['evolves_to'][0].get('evolution_details', [{}])[0].get('min_level', 999)}
                    for evo in chain['evolves_to']:
                        if evo['species']['name'] == name.lower() and evo['evolves_to']:
                            return {'evolves_to': evo['evolves_to'][0]['species']['name'], 
                                    'level': evo['evolves_to'][0].get('evolution_details', [{}])[0].get('min_level', 999)}
    return None