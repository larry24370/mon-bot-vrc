import os
import asyncio
import discord
from aiohttp import web

# ==========================================
# TES CONFIGURATIONS (Colle tes infos ici)
# ==========================================
TOKEN = MTU1MDg4NDM4NzUxODgxMjE2MA.GImHPV.MXbAqoj7_8pdo3ae1Ez7mwspLNSo4_6Y2jdpfQ
CHANNEL_ID = 1550862745933578350  # (Exemple : 123456789012345678, sans guillemets)
# ==========================================

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Mémoire pour stocker la dernière photo
derniere_image = None
format_image = "image/png"

@client.event
async def on_ready():
    print("=" * 40)
    print(f"✅ Bot connecte avec succes : {client.user}")
    print(f"👀 En ecoute dans le salon ID : {CHANNEL_ID}")
    print("=" * 40)

@client.event
async def on_message(message):
    global derniere_image, format_image

    # Ignorer les messages des bots et vérifier qu'on est dans le bon salon
    if message.author.bot or message.channel.id != CHANNEL_ID:
        return

    # Si le message contient un fichier (photo)
    if message.attachments:
        piece_jointe = message.attachments[0]
        # Vérifie que c'est bien une image
        if any(piece_jointe.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
            print(f"📸 Nouvelle photo recue de {message.author.name} !")
            
            # Télécharge l'image en mémoire
            derniere_image = await piece_jointe.read()
            format_image = piece_jointe.content_type or "image/png"
            
            # Ajoute une réaction ✅ sur Discord pour confirmer que c'est bien reçu
            await message.add_reaction("✅")

# Serveur Web qui donne l'image à VRChat
async def servir_photo(request):
    global derniere_image, format_image
    if derniere_image is None:
        return web.Response(text="Aucune photo envoyee pour le moment.", status=404)
    
    return web.Response(body=derniere_image, content_type=format_image, headers={
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache"
    })

async def main():
    # Démarre le serveur Web
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get('/photo.png', servir_photo)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    # Démarre le Bot Discord
    await client.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
