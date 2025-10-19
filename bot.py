import discord
import os                 # Pour lire les variables d'environnement
from dotenv import load_dotenv  # Pour charger le fichier .env en local

# --- CHARGEMENT DES VARIABLES ---
load_dotenv() # Charge les variables du fichier .env (pour les tests locaux)
TOKEN = os.getenv('DISCORD_TOKEN') # Récupère le token

# Vérification si le token existe
if TOKEN is None:
    print("ERREUR : Le 'DISCORD_TOKEN' n'est pas trouvé.")
    print("Veuillez vérifier votre fichier .env ou les variables d'environnement sur Railway.")
    exit()

# --- CONFIGURATION DES INTENTS ---
# On définit ce à quoi le bot a le droit de réagir
intents = discord.Intents.default()
intents.members = True          # Pour les événements d'arrivée/départ de membres
intents.message_content = True  # Pour lire le contenu des messages (ex: !ping)

# --- INITIALISATION DU BOT ---
client = discord.Client(intents=intents)

# --- ÉVÉNEMENTS DISCORD ---

@client.event
async def on_ready():
    """Appelé quand le bot est connecté et prêt."""
    print(f'Connecté en tant que {client.user}!')
    print(f'ID: {client.user.id}')
    print('------')

@client.event
async def on_message(message):
    """Appelé à chaque fois qu'un message est envoyé."""
    
    # Ignore les messages envoyés par le bot lui-même
    if message.author == client.user:
        return

    # Commande !ping
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')

    # Commande !hello
    if message.content.startswith('!hello'):
        await message.channel.send(f'Bonjour, {message.author.mention} !')

# --- DÉMARRAGE DU BOT ---
try:
    client.run(TOKEN)
except discord.errors.LoginFailure:
    print("ERREUR : Le token est invalide. Vérifiez-le.")
except Exception as e:
    print(f"Une erreur inattendue est survenue : {e}")