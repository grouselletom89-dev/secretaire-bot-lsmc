import discord
import os
from dotenv import load_dotenv

# --- CHARGEMENT DES VARIABLES ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    print("ERREUR : Le 'DISCORD_TOKEN' n'est pas trouvé.")
    print("Veuillez vérifier votre fichier .env ou les variables d'environnement sur Railway.")
    exit()

# --- CONFIGURATION ---

# ID du salon où le message de l'organigramme doit être
TARGET_CHANNEL_ID = 1418570285841645588

# On utilise une LISTE de tuples (ID_ROLE, TEXTE_A_AFFICHER)
ROLES_A_SUIVRE_CONFIG = [
    (1417261983773753518, "🧬 | Responsable Morgue :"),
    (1418566218171945050, "🚁 | Responsable Hélico :"),
    (1388532907592908871, "🧠 | Responsable Psychologie :"),
    (1417670797534957681, "🧪 | Responsable Labo :"),
    (1417671433412284426, "🩹 | Responsable Advanced Medecine :"),
    (1418564885662666853, "🅾️ | Responsable E.M.T. :"),
    (1388532909434212362, "📕 | Responsable du CNOM :"),
    (1388532912734867496, "🗂️ | Responsable Recrutement / Formations :")
]

# On crée un 'set' (ensemble) de tous les ID de rôles valides.
ROLE_IDS_A_SUIVRE = {role_id for role_id, text in ROLES_A_SUIVRE_CONFIG if role_id is not None}

# --- VARIABLES GLOBALES ---
organigram_message = None

# --- CONFIGURATION DES INTENTS ---
intents = discord.Intents.default()
intents.members = True          # OBLIGATOIRE pour on_member_update et guild.get_role
intents.message_content = True  # Pour les commandes !ping

# --- INITIALISATION DU BOT ---
client = discord.Client(intents=intents)

# --- FONCTION : Mettre à jour l'organigramme ---

async def update_organigram():
    global organigram_message
    if organigram_message is None:
        print("Erreur : Tentative de mise à jour sans message d'organigramme.")
        return

    guild = organigram_message.guild  # Récupère le serveur
    lines = [] # On va construire le message ligne par ligne

    # --- Construction du message ---
    lines.append("**Liste des Gérants et leurs Pôles :**\n")
    
    # LA LIGNE `@ ────── Pôle EMS ──────` A ÉTÉ SUPPRIMÉE ICI

    # Boucle sur notre LISTE de configuration pour garder l'ordre
    for role_id, display_text in ROLES_A_SUIVRE_CONFIG:
        
        mentions = " " # Par défaut, la ligne est vide

        if role_id is None:
            mentions = " "
        else:
            role = guild.get_role(role_id)
        
            if role is None:
                print(f"ATTENTION : Le rôle ID {role_id} est introuvable sur le serveur.")
                mentions = "`(Rôle introuvable)`"
            else:
                members = role.members
                if members:
                    mentions = " / ".join([member.mention for member in members])
        
        # Ajoute la ligne au message (avec l'emoji)
        lines.append(f"{display_text} {mentions}")

    # Combine toutes les lignes en un seul message
    content = "\n".join(lines)
    
    # Edite le message sur Discord
    try:
        await organigram_message.edit(content=content)
    except Exception as e:
        print(f"Erreur lors de l'édition du message : {e}")


# --- ÉVÉNEMENTS DISCORD ---

@client.event
async def on_ready():
    """Appelé quand le bot est connecté et prêt."""
    global organigram_message
    
    print(f'Connecté en tant que {client.user}!')
    print('------')

    channel = client.get_channel(TARGET_CHANNEL_ID)
    
    if channel is None:
        print(f"ERREUR CRITIQUE : Le canal avec l'ID {TARGET_CHANNEL_ID} est introuvable.")
        return

    print(f"Recherche du message dans le canal #{channel.name}...")
    
    try:
        await channel.purge(limit=100, check=lambda m: m.author == client.user)
        print("Anciens messages du bot nettoyés.")
    except discord.errors.Forbidden:
        print("ERREUR : Le bot n'a pas la permission 'Gérer les messages' pour nettoyer le salon.")
    except Exception as e:
        print(f"Erreur lors du nettoyage : {e}")

    organigram_message = await channel.send("Initialisation de la liste des pôles...")
    print(f"Message d'organigramme créé (ID: {organigram_message.id}).")
    
    await update_organigram()
    print("Organigramme initialisé et mis à jour.")


@client.event
async def on_member_update(before, after):
    """Appelé quand un membre est mis à jour (rôles, pseudo, etc.)."""
    
    if before.roles == after.roles:
        return 

    roles_modifies = set(before.roles) ^ set(after.roles)
    
    pertinent = False
    for role in roles_modifies:
        if role.id in ROLE_IDS_A_SUIVRE:
            pertinent = True
            break 

    if pertinent:
        print(f"Mise à jour de l'organigramme car {after.display_name} a eu un changement de rôle.")
        await update_organigram()


@client.event
async def on_message(message):
    """Appelé à chaque fois qu'un message est envoyé."""
    
    if message.author == client.user:
        return

    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')


# --- DÉMARRAGE DU BOT ---
try:
    client.run(TOKEN)
except Exception as e:
    print(f"Une erreur fatale est survenue au lancement : {e}")
