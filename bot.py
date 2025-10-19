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

# Ce dictionnaire fait le lien entre le NOM EXACT du rôle et ce qui doit être affiché.
# IMPORTANT : Le nom du rôle (à gauche) doit être PARFAITEMENT identique à celui sur Discord.
# (majuscules, espaces, emojis s'il y en a dans le nom)
# J'ai copié les emojis et le texte depuis votre screenshot.
ROLES_A_SUIVRE = {
    "Responsable Morgue": "🧬 | Responsable Morgue :",
    "Responsable Hélico": "🚁 | Responsable Hélico :",
    "Responsable Psychologie": "🧠 | Responsable Psychologie :",
    "Responsable Labo": "🧪 | Responsable Labo :",
    "Responsable Advanced Medecine": "🩹 | Responsable Advanced Medecine :",
    "Responsable E.M.T.": "🅾️ | Responsable E.M.T. :",
    "Responsable du CNOM": "📕 | Responsable du CNOM :",
    "Responsable Recrutement / Formations": "🗂️ | Responsable Recrutement / Formations :"
}

# --- VARIABLES GLOBALES ---
# On stockera le message de l'organigramme ici pour pouvoir l'éditer
organigram_message = None

# --- CONFIGURATION DES INTENTS ---
# On s'assure que les intents 'members' et 'message_content' sont bien activés
intents = discord.Intents.default()
intents.members = True          # OBLIGATOIRE pour on_member_update
intents.message_content = True  # Pour les commandes !ping

# --- INITIALISATION DU BOT ---
client = discord.Client(intents=intents)

# --- NOUVELLE FONCTION : Mettre à jour l'organigramme ---

async def update_organigram():
    global organigram_message
    if organigram_message is None:
        print("Erreur : Tentative de mise à jour sans message d'organigramme.")
        return

    guild = organigram_message.guild  # Récupère le serveur
    lines = [] # On va construire le message ligne par ligne

    # --- Construction du message ---
    lines.append("**Liste des Gérants et leurs Pôles :**\n")
    lines.append("`@ ────── Pôle EMS ──────`\n") # J'imite le style de votre screen

    # Boucle sur notre dictionnaire de configuration
    for role_name, display_text in ROLES_A_SUIVRE.items():
        
        # Trouve le rôle sur le serveur par son nom
        role = discord.utils.get(guild.roles, name=role_name)
        
        if role is None:
            # Si le rôle n'est pas trouvé sur le serveur
            print(f"ATTENTION : Le rôle '{role_name}' est introuvable sur le serveur.")
            mentions = "`(Rôle non trouvé)`"
        else:
            # Si le rôle est trouvé, on liste les membres qui l'ont
            members = role.members
            if not members:
                # Personne n'a le rôle
                mentions = " " # Laisse vide comme sur votre screen
            else:
                # Construit la liste des mentions (ex: @User1 / @User2)
                mentions = " / ".join([member.mention for member in members])
        
        # Ajoute la ligne au message
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
    print(f'ID: {client.user.id}')
    print('------')

    # --- Initialisation du message de l'organigramme ---
    channel = client.get_channel(TARGET_CHANNEL_ID)
    
    if channel is None:
        print(f"ERREUR CRITIQUE : Le canal avec l'ID {TARGET_CHANNEL_ID} est introuvable.")
        print("Vérifiez l'ID ou les permissions du bot (doit pouvoir voir le salon).")
        return

    print(f"Recherche du message dans le canal #{channel.name}...")
    
    # Nettoie les anciens messages du bot dans ce salon pour éviter les doublons
    try:
        await channel.purge(limit=100, check=lambda m: m.author == client.user)
        print("Anciens messages du bot nettoyés.")
    except discord.errors.Forbidden:
        print("ERREUR : Le bot n'a pas la permission 'Gérer les messages' pour nettoyer le salon.")
        print("Recherche d'un message existant...")
        # (Alternative si purge échoue, mais plus complexe - on crée un nouveau message)
    except Exception as e:
        print(f"Erreur lors du nettoyage : {e}")

    # Crée le nouveau message
    organigram_message = await channel.send("Initialisation de la liste des pôles...")
    print(f"Message d'organigramme créé (ID: {organigram_message.id}).")
    
    # Lance la première mise à jour
    await update_organigram()
    print("Organigramme initialisé et mis à jour.")


@client.event
async def on_member_update(before, after):
    """Appelé quand un membre est mis à jour (rôles, pseudo, etc.)."""
    
    # 1. On vérifie si les rôles ont changé
    if before.roles == after.roles:
        return # Pas de changement de rôle, on s'arrête là

    # 2. On regarde quels rôles ont été ajoutés ou retirés
    # (set(before.roles) ^ set(after.roles)) donne les rôles différents
    roles_modifies = set(before.roles) ^ set(after.roles)
    
    # 3. On vérifie si UN de ces rôles modifiés est dans notre liste ROLES_A_SUIVRE
    pertinent = False
    for role in roles_modifies:
        if role.name in ROLES_A_SUIVRE:
            pertinent = True
            break # Un seul rôle pertinent suffit

    # 4. Si le changement est pertinent, on met à jour le message
    if pertinent:
        print(f"Mise à jour de l'organigramme car {after.display_name} a eu un changement de rôle.")
        await update_organigram()


@client.event
async def on_message(message):
    """Appelé à chaque fois qu'un message est envoyé."""
    
    # Ignore les messages envoyés par le bot lui-même
    if message.author == client.user:
        return

    # Commande !ping (toujours utile pour tester)
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')


# --- DÉMARRAGE DU BOT ---
try:
    client.run(TOKEN)
except Exception as e:
    print(f"Une erreur fatale est survenue au lancement : {e}")
