import discord
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz 

# --- CHARGEMENT DES VARIABLES ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    print("ERREUR : Le 'DISCORD_TOKEN' n'est pas trouvé.")
    exit()

# =======================================================================
# --- CONFIGURATION ORGANI. EMS ---
# =======================================================================
EMS_CHANNEL_ID = 1418570285841645588
EMS_ROLES_IDS = [
    1417261983773753518, # Responsable Morgue
    1418566218171945050, # Responsable Hélico
    1388532907592908871, # Responsable Psychologie
    1417670797534957681, # Responsable Labo
    1417671433412284426, # Responsable Advanced Medecine
    1418564885662666853, # Responsable E.M.T.
    1388532909434212362, # Responsable du CNOM
    1388532912734867496  # Responsable Recrutement / Formations
]
EMS_ROLES_IDS_SET = set(EMS_ROLES_IDS)

# =======================================================================
# --- CONFIGURATION HIÉRARCHIE ---
# =======================================================================
HIERARCHIE_CHANNEL_ID = 1388975591117557941
HIERARCHIE_ROLES_IDS = [
    1349780660138541078, # Directeur de Centre
    1388532898705178746, # Co-Directeur
    1388532894582181939, # Directeur des ressources Humaines
    1388532896309973052, # Ressource Humaine
    1388532899229339820, # Chef de service
    1388532949753925672, # Médecin Chef
    1388532896993906772, # Médecin
    1388532900571386076, # Infirmier
    1388532902949683401  # Ambulancier
]
HIERARCHIE_ROLES_IDS_SET = set(HIERARCHIE_ROLES_IDS)

# =======================================================================
# --- NOUVEAU : CONFIGURATION DU SERMENT ---
# =======================================================================
SERMENT_CHANNEL_ID = 1370016292316123186
SERMENT_TEXT = """« Je jure de consacrer ma vie à la pratique de l’art médical avec conscience, dignité et humanité.

Je m’engage à mettre mes connaissances et mes compétences au service de la vie humaine, en priorité pour le bien-être de mes patients, sans jamais chercher à nuire ou à infliger volontairement un préjudice.

Je respecterai la vie humaine dès sa conception, en toutes circonstances, et je traiterai chaque patient avec équité, respect et compassion.

Je préserverai la confidentialité de tous ceux qui me confient leur santé et leur vie, en honorant leur confiance.

Je reconnais et respecterai mes maîtres, mes collègues et tous ceux qui m’ont précédé dans l’art de guérir, et je m’efforcerai de partager mon savoir avec les générations futures pour que le savoir médical continue de progresser.

Je m’engage à rester humble et à perfectionner mes compétences tout au long de ma carrière, en tenant compte des avancées scientifiques et des besoins de mes patients.

Je pratiquerai mon métier avec honnêteté, intégrité et responsabilité, en veillant toujours à ce que ma conduite soit guidée par l’éthique, le respect de la vie et la dignité humaine.

Que je sois honoré si je respecte ce serment, et que je sois confronté à l’inverse si je le viole. Que mes actes soient toujours au service de la santé et de l’humanité. »"""


# --- VARIABLES GLOBALES ---
ems_organigram_message = None
hierarchie_message = None

# --- CONFIGURATION DES INTENTS ---
intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

# --- INITIALISATION DU BOT ---
client = discord.Client(intents=intents)

# =======================================================================
# --- FONCTION : Mettre à jour l'organigramme EMS ---
# =======================================================================
async def update_organigram_ems():
    global ems_organigram_message
    if ems_organigram_message is None: return

    guild = ems_organigram_message.guild
    lines = ["**Liste des Gérants et leurs Pôles :**\n"]

    for role_id in EMS_ROLES_IDS:
        role = guild.get_role(role_id)
        mentions = " "
        display_name = f"`(Rôle ID {role_id} introuvable)`"

        if role is not None:
            display_name = role.mention
            members = role.members
            if members:
                mentions = " / ".join([member.mention for member in members])
        else:
            print(f"ATTENTION (EMS) : Le rôle ID {role_id} est introuvable.")
        
        lines.append(f"{display_name} : {mentions}")

    try:
        await ems_organigram_message.edit(content="\n".join(lines))
    except Exception as e:
        print(f"Erreur lors de l'édition du message EMS : {e}")

# =======================================================================
# --- FONCTION : Mettre à jour la Hiérarchie ---
# =======================================================================
async def update_hierarchie():
    global hierarchie_message
    if hierarchie_message is None: return

    guild = hierarchie_message.guild
    lines = ["### Hiérarchie\n"] 

    members_deja_affiches = set()

    for role_id in HIERARCHIE_ROLES_IDS:
        role = guild.get_role(role_id)
        
        if role is not None:
            lines.append(f"{role.mention}")
            
            tous_les_membres_du_role = role.members
            membres_a_afficher = []
            
            for member in tous_les_membres_du_role:
                if member.id not in members_deja_affiches:
                    membres_a_afficher.append(member)
                    members_deja_affiches.add(member.id)
            
            if not membres_a_afficher:
                lines.append("> Aucun membre\n") 
            else:
                member_mentions = [member.mention for member in membres_a_afficher]
                lines.append(f"> {' | '.join(member_mentions)}\n")
        else:
            print(f"ATTENTION (Hiérarchie) : Le rôle ID {role_id} est introuvable.")
            lines.append(f"`(Rôle ID {role_id} introuvable)`\n")

    try:
        paris_tz = pytz.timezone("Europe/Paris")
        now = datetime.now(paris_tz)
        timestamp = now.strftime("%d/%m/%Y à %HH%M")
        lines.append(f"\n*Mise à jour le {timestamp} (Heure de Paris)*")
    except Exception as e:
        print(f"Erreur lors de la récupération de l'heure : {e}")
        lines.append(f"\n*Mise à jour (heure non disponible)*")

    try:
        allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=True)
        await hierarchie_message.edit(content="\n".join(lines), allowed_mentions=allowed_mentions)
    except Exception as e:
        print(f"Erreur lors de l'édition du message Hiérarchie : {e}")


# =======================================================================
# --- ÉVÉNEMENTS DISCORD ---
# =======================================================================

@client.event
async def on_ready():
    """Appelé quand le bot est connecté et prêt."""
    global ems_organigram_message, hierarchie_message
    
    print(f'Connecté en tant que {client.user}!')
    print('------')

    # --- Initialisation Message 1: Organigramme EMS ---
    channel_ems = client.get_channel(EMS_CHANNEL_ID)
    if channel_ems:
        print(f"Nettoyage du canal EMS #{channel_ems.name}...")
        try:
            await channel_ems.purge(limit=100, check=lambda m: m.author == client.user)
            ems_organigram_message = await channel_ems.send("Initialisation EMS...")
            await update_organigram_ems()
            print("Organigramme EMS initialisé.")
        except Exception as e:
            print(f"Erreur lors de l'init EMS : {e}")
    else:
        print(f"ERREUR CRITIQUE : Canal EMS ID {EMS_CHANNEL_ID} introuvable.")

    # --- Initialisation Message 2: Hiérarchie ---
    channel_hierarchie = client.get_channel(HIERARCHIE_CHANNEL_ID)
    if channel_hierarchie:
        print(f"Nettoyage du canal Hiérarchie #{channel_hierarchie.name}...")
        try:
            await channel_hierarchie.purge(limit=100, check=lambda m: m.author == client.user)
            hierarchie_message = await channel_hierarchie.send("Initialisation Hiérarchie...")
            await update_hierarchie()
            print("Hiérarchie initialisée.")
        except Exception as e:
            print(f"Erreur lors de l'init Hiérarchie : {e}")
    else:
        print(f"ERREUR CRITIQUE : Canal Hiérarchie ID {HIERARCHIE_CHANNEL_ID} introuvable.")

    # --- NOUVEAU : Initialisation Message 3: Serment ---
    channel_serment = client.get_channel(SERMENT_CHANNEL_ID)
    if channel_serment:
        print(f"Nettoyage du canal Serment #{channel_serment.name}...")
        try:
            # On nettoie les anciens messages du bot
            await channel_serment.purge(limit=100, check=lambda m: m.author == client.user)
            # On poste le nouveau
            await channel_serment.send(SERMENT_TEXT)
            print("Serment d'Hippocrate posté.")
        except Exception as e:
            print(f"Erreur lors de l'init Serment : {e}")
    else:
        print(f"ERREUR CRITIQUE : Canal Serment ID {SERMENT_CHANNEL_ID} introuvable.")
    
    print("------\nBot prêt !")


@client.event
async def on_member_update(before, after):
    """Appelé quand un membre est mis à jour (rôles, pseudo, etc.)."""
    
    if before.roles == after.roles:
        return 

    roles_modifies = set(before.roles) ^ set(after.roles)
    
    # Vérification pour EMS
    ems_pertinent = False
    for role in roles_modifies:
        if role.id in EMS_ROLES_IDS_SET:
            ems_pertinent = True
            break
            
    if ems_pertinent:
        print(f"Mise à jour EMS (membre : {after.display_name}).")
        await update_organigram_ems()

    # Vérification pour Hiérarchie
    hierarchie_pertinente = False
    for role in roles_modifies:
        if role.id in HIERARCHIE_ROLES_IDS_SET:
            hierarchie_pertinente = True
            break
            
    if hierarchie_pertinente:
        print(f"Mise à jour Hiérarchie (membre : {after.display_name}).")
        await update_hierarchie()


@client.event
async def on_message(message):
    """Appelé à chaque fois qu'un message est envoyé."""
    if message.author == client.user: return
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')

# --- DÉMARRAGE DU BOT ---
try:
    client.run(TOKEN)
except Exception as e:
    print(f"Une erreur fatale est survenue au lancement : {e}")
