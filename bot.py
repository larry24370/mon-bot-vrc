import os
import io
import asyncio
import discord
from aiohttp import web

TOKEN = os.environ.get("DISCORD_TOKEN")

# ==========================================
# CONFIGURATION DES SALONS
# ==========================================
SALON_PUBLIC = "photos"      # Là où les gens déposent les photos
SALON_ARCHIVE = "archives"   # Ton salon secret où elles sont stockées
# ==========================================

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

derniere_image = None
format_image = "image/png"

@client.event
async def on_ready():
    print("=" * 40, flush=True)
    print(f"✅ Bot connecte : {client.user}", flush=True)
    print(f"👀 En ecoute dans #{SALON_PUBLIC} -> Transfert vers #{SALON_ARCHIVE}", flush=True)
    print("=" * 40, flush=True)

@client.event
async def on_message(message):
    global derniere_image, format_image

    # 1. Ignorer les messages des bots
    if message.author.bot:
        return

    # 2. On n'écoute QUE le salon "photos"
    if message.channel.name != SALON_PUBLIC:
        return

    # 3. Si le message contient une photo
    if message.attachments:
        piece_jointe = message.attachments[0]
        if any(piece_jointe.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
            print(f"📸 Photo recue de {message.author.name}, transfert en cours...", flush=True)

            # A. Télécharge l'image en mémoire
            image_bytes = await piece_jointe.read()
            content_type = piece_jointe.content_type or "image/png"

            # B. Cherche ton salon secret "archives" et reposte la photo dedans
            salon_archive = discord.utils.get(message.guild.channels, name=SALON_ARCHIVE)
            if salon_archive:
                fichier = discord.File(io.BytesIO(image_bytes), filename=piece_jointe.filename)
                await salon_archive.send(
                    content=f"📸 **Photo envoyée par :** {message.author.mention} (`{message.author.name}`)",
                    file=fichier
                )

            # C. Supprime immédiatement la photo de "#photos" pour que personne ne la voie !
            try:
                await message.delete()
            except Exception as e:
                print(f"Erreur suppression : {e}", flush=True)

            # D. Met à jour l'image pour VRChat
            derniere_image = image_bytes
            format_image = content_type
            print("✨ Image transmise a VRChat avec succes !", flush=True)

# Serveur Web pour VRChat
async def servir_photo(request):
    global derniere_image, format_image
    if derniere_image is None:
        return web.Response(text="Aucune photo envoyee pour le moment.", status=404)
    
    return web.Response(body=derniere_image, content_type=format_image, headers={
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache"
    })

async def main():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get('/photo.png', servir_photo)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    await client.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
