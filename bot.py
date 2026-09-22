import os
import io
import asyncio
import discord
from aiohttp import web
from PIL import Image, ImageOps

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

def traiter_image_pour_vrchat(image_bytes: bytes) -> bytes:
    """Répare la photo pour VRChat (Noir & Blanc, orientation, format standard)."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        # Corrige l'orientation automatique des téléphones
        img = ImageOps.exif_transpose(img)

        # Répare le bug des photos Snapchat noir et blanc en forçant le mode couleur RGBA
        if img.mode != "RGBA" and img.mode != "RGB":
            img = img.convert("RGBA")

        # Sauvegarde en vrai PNG standard
        sortie = io.BytesIO()
        img.save(sortie, format="PNG")
        return sortie.getvalue()

@client.event
async def on_ready():
    print("=" * 40, flush=True)
    print(f"✅ Bot connecte : {client.user}", flush=True)
    print(f"👀 En ecoute dans #{SALON_PUBLIC} -> Transfert vers #{SALON_ARCHIVE}", flush=True)
    print("=" * 40, flush=True)

@client.event
async def on_message(message):
    global derniere_image

    # 1. Ignorer les messages des bots
    if message.author.bot:
        return

    # 2. On n'écoute QUE le salon "photos"
    if message.channel.name != SALON_PUBLIC:
        return

    # 3. Si le message contient une photo
    if message.attachments:
        piece_jointe = message.attachments[0]
        extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
        
        if any(piece_jointe.filename.lower().endswith(ext) for ext in extensions):
            print(f"📸 Photo recue de {message.author.name}, traitement en cours...", flush=True)

            try:
                # A. Télécharge l'image originale
                image_brute = await piece_jointe.read()

                # B. Corrige et convertit l'image pour VRChat (gère le noir et blanc)
                image_corrigee = traiter_image_pour_vrchat(image_brute)

                # C. Cherche le salon secret "archives" et poste l'ORIGINALE
                salon_archive = discord.utils.get(message.guild.channels, name=SALON_ARCHIVE)
                if salon_archive:
                    fichier = discord.File(io.BytesIO(image_brute), filename=piece_jointe.filename)
                    await salon_archive.send(
                        content=f"📸 **Photo envoyée par :** {message.author.mention} (`{message.author.name}`)",
                        file=fichier
                    )

                # D. Supprime la photo du salon public
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Erreur suppression : {e}", flush=True)

                # E. Met à jour l'image pour VRChat
                derniere_image = image_corrigee
                print("✨ Image transmise a VRChat avec succes !", flush=True)

            except Exception as e:
                print(f"❌ Erreur : {e}", flush=True)

# Serveur Web pour VRChat
async def servir_photo(request):
    global derniere_image, format_image
    if derniere_image is None:
        return web.Response(text="Aucune photo envoyee pour le moment.", status=404)
    
    return web.Response(
        body=derniere_image, 
        content_type=format_image, 
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )

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
