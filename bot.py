import os
import asyncio
import discord
from aiohttp import web

TOKEN = os.environ.get("DISCORD_TOKEN")

# ==========================================
# NOM DU SALON RÉSERVÉ AUX PHOTOS
# ==========================================
NOM_DU_SALON = "photos"
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
    print(f"👀 En ecoute EXCLUSIVE dans le salon #{NOM_DU_SALON}", flush=True)
    print("=" * 40, flush=True)

@client.event
async def on_message(message):
    global derniere_image, format_image

    # 1. On ignore les bots
    if message.author.bot:
        return

    # 2. VÉRIFICATION STRICTE : On ignore TOUS les salons sauf "#photos" !
    if message.channel.name != NOM_DU_SALON:
        return

    # 3. Si le message contient une photo
    if message.attachments:
        piece_jointe = message.attachments[0]
        if any(piece_jointe.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
            print(f"📸 Photo validee recue dans #{NOM_DU_SALON} de {message.author.name} !", flush=True)
            
            # Télécharge la photo en mémoire
            derniere_image = await piece_jointe.read()
            format_image = piece_jointe.content_type or "image/png"
            
            # Ajoute le ✅ sous la photo sur Discord
            await message.add_reaction("✅")

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
