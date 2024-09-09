import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime

# Configuration du bot Discord
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Variables globales pour les deux streams
day_stream_url = 'http://stream.priyom.org:8000/wheel-day.ogg'  # URL du stream pour la journée
night_stream_url = 'http://stream.priyom.org:8000/wheel-night.ogg'  # URL du stream pour la nuit
current_period = None  # Pour garder une trace si c'est le jour ou la nuit

# Fonction pour jouer un stream selon l'heure
async def play_stream(vc, stream_url):
    if not vc.is_playing():
        stream_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(stream_url))
        vc.play(stream_source)
    else:
        print("Stream already playing.")

# Fonction pour déterminer si c'est le jour ou la nuit
def is_daytime():
    current_time = datetime.now().time()
    # Si l'heure est entre 07:00 et 18:00, c'est le jour
    return current_time >= datetime.strptime("07:00", "%H:%M").time() and current_time < datetime.strptime("18:00", "%H:%M").time()

# Fonction pour gérer la transition entre le jour et la nuit
async def check_time_and_switch_stream(vc):
    global current_period

    if is_daytime() and current_period != "day":
        print("Switching to daytime stream")
        current_period = "day"
        if vc.is_playing():
            vc.stop()  # Arrêter le stream actuel
        await asyncio.sleep(10)  # Attendre 10 secondes avant de jouer le nouveau stream
        await play_stream(vc, day_stream_url)

    elif not is_daytime() and current_period != "night":
        print("Switching to nighttime stream")
        current_period = "night"
        if vc.is_playing():
            vc.stop()  # Arrêter le stream actuel
        await asyncio.sleep(10)  # Attendre 10 secondes avant de jouer le nouveau stream
        await play_stream(vc, night_stream_url)

# Event on_ready pour afficher que le bot est prêt et rejoindre le canal vocal automatiquement
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    # Parcourir tous les serveurs auxquels le bot est connecté
    for guild in bot.guilds:
        # Sélectionner le bon canal vocal et URL de stream selon l'heure
        voice_channel_name = "TheWheel Day" if is_daytime() else "TheWheel Night"
        stream_url = day_stream_url if is_daytime() else night_stream_url
        global current_period
        current_period = "day" if is_daytime() else "night"

        # Vérifier si un salon vocal correspondant existe
        voice_channel = discord.utils.get(guild.voice_channels, name=voice_channel_name)

        if voice_channel:
            # Si déjà connecté, déconnecter d'abord
            if guild.voice_client and guild.voice_client.is_connected():
                await guild.voice_client.disconnect()

            # Connecter le bot au salon vocal
            vc = await voice_channel.connect()

            # Attendre 10 secondes avant de diffuser
            await asyncio.sleep(10)
            await play_stream(vc, stream_url)
        else:
            # Créer le canal vocal s'il n'existe pas
            voice_channel = await guild.create_voice_channel(voice_channel_name)
            vc = await voice_channel.connect()

            # Attendre 10 secondes avant de diffuser
            await asyncio.sleep(10)
            await play_stream(vc, stream_url)

        # Boucle pour vérifier toutes les minutes si le stream doit être changé
        while True:
            await asyncio.sleep(60)  # Vérification toutes les minutes
            await check_time_and_switch_stream(vc)

# Le token est récupéré depuis une variable d'environnement
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
