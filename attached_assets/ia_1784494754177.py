import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import re

# Configuración de Autopy AI basada en tu documentación
AUTOPY_API_KEY = "apt_RXae3prqggV5Fa52bmgao1A8s2mX9PQKSrh7WvXX"  # Reemplaza con tu token 'apt_...'
AUTOPY_BASE_URL = "https://autopy-ia.onrender.com/api/v1/chat"

# Base de datos simulada en memoria (Guarda la configuración indexada por Canal ID)
ia_channels_config = {}

def get_channel_config(channel_id):
    if channel_id not in ia_channels_config:
        ia_channels_config[channel_id] = {
            "active": False,
            "webhook_url": None,
            "nombre": "Autopy AI",
            "avatar_url": "https://i.imgur.com/wSTFkRM.png", # Avatar por defecto
            "personalidad": "Eres un asistente útil y amigable.",
            "historial": []
        }
    return ia_channels_config[channel_id]


# --- MODALES PARA LA INTERFAZ ---

class SetWebhookModal(discord.ui.Modal, title="Establecer Canal e IA"):
    channel_id_input = discord.ui.TextInput(
        label="ID del Canal de Texto",
        placeholder="Ej. 112233445566778899",
        required=True,
        max_length=25
    )
    url_input = discord.ui.TextInput(
        label="URL del Webhook de Discord", 
        placeholder="https://discord.com/api/webhooks/...", 
        required=True
    )

    def __init__(self, current_channel_id, refresh_callback):
        super().__init__()
        self.current_channel_id = current_channel_id
        self.refresh_callback = refresh_callback

    async def on_submit(self, interaction: discord.Interaction):
        url = self.url_input.value.strip()
        target_channel_id_str = self.channel_id_input.value.strip()
        
        # Validar que el ID del canal sea numérico
        if not target_channel_id_str.isdigit():
            await interaction.response.send_message("❌ El ID del canal debe contener solo números.", ephemeral=True)
            return
            
        target_channel_id = int(target_channel_id_str)

        # Validación de URL de webhook de Discord
        if not re.match(r"^https://(canary\.|ptb\.)?discord\.com/api/webhooks/\d+/\S+", url):
            await interaction.response.send_message("❌ La URL proporcionada no es un Webhook de Discord válido.", ephemeral=True)
            return

        # Guardamos la configuración apuntando al ID del canal especificado
        config = get_channel_config(target_channel_id)
        config["webhook_url"] = url
        config["active"] = True 
        
        await interaction.response.send_message(f"✅ Canal <#{target_channel_id}> enlazado con éxito. La IA responderá allí sin comandos.", ephemeral=True)
        # Actualizamos el panel visual usando el ID del canal objetivo
        await self.refresh_callback(interaction, target_channel_id)


class EditWebhookIdentityModal(discord.ui.Modal, title="Editar Identidad del Webhook"):
    name_input = discord.ui.TextInput(label="Nombre de la IA", placeholder="Ej. Jarvis", max_length=50, required=True)
    avatar_input = discord.ui.TextInput(label="URL de la Foto de Perfil (Link)", placeholder="https://link-de-la-imagen.png", required=False)
    personality_input = discord.ui.TextInput(
        label="Personalidad / Prompt de Sistema",
        style=discord.TextStyle.paragraph,
        placeholder="Ej. Eres un robot sarcástico...",
        max_length=400,
        required=True
    )

    def __init__(self, channel_id, refresh_callback):
        super().__init__()
        self.channel_id = channel_id
        self.refresh_callback = refresh_callback
        
        # Prellenar con los valores actuales
        config = get_channel_config(channel_id)
        self.name_input.default = config["nombre"]
        self.avatar_input.default = config["avatar_url"]
        self.personality_input.default = config["personalidad"]

    async def on_submit(self, interaction: discord.Interaction):
        config = get_channel_config(self.channel_id)
        config["nombre"] = self.name_input.value
        if self.avatar_input.value:
            config["avatar_url"] = self.avatar_input.value
        config["personalidad"] = self.personality_input.value
        
        await interaction.response.send_message("✅ Identidad y personalidad actualizadas correctamente.", ephemeral=True)
        await self.refresh_callback(interaction, self.channel_id)


# --- PANEL DE CONTROL (VISTA) ---

class IAControlView(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    async def update_embed(self, interaction: discord.Interaction, target_channel_id=None):
        if target_channel_id:
            self.channel_id = target_channel_id
            
        config = get_channel_config(self.channel_id)
        status_text = "🟢 ACTIVO (Responde a todo)" if config["active"] and config["webhook_url"] else "🔴 INACTIVO"
        
        embed = discord.Embed(
            title="🤖 Panel de Configuración de IA por Canal",
            description="Controla el comportamiento automatizado de la IA mediante Webhooks en tiempo real.",
            color=0x2F3136
        )
        embed.add_field(name="Canal Registrado", value=f"<#{self.channel_id}> (`{self.channel_id}`)", inline=False)
        embed.add_field(name="Estado del canal", value=f"`{status_text}`", inline=True)
        embed.add_field(name="Nombre del Webhook", value=f"`{config['nombre']}`", inline=True)
        embed.add_field(name="Prompt de Personalidad", value=f"*{config['personalidad']}*", inline=False)
        
        if config["avatar_url"] and config["avatar_url"].startswith("http"):
            embed.set_thumbnail(url=config["avatar_url"])
            
        embed.set_footer(text="Autopy AI — Modo Webhook Activo")
        
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Establecer Canal / Webhook", style=discord.ButtonStyle.success, emoji="🔗")
    async def set_webhook(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetWebhookModal(self.channel_id, self.update_embed))

    @discord.ui.button(label="Editar Webhook (Perfil/Nombre)", style=discord.ButtonStyle.primary, emoji="🎭")
    async def edit_webhook_identity(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditWebhookIdentityModal(self.channel_id, self.update_embed))

    @discord.ui.button(label="Eliminar Chat IA", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def clear_chat(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_channel_config(self.channel_id)
        config["historial"] = []
        await interaction.response.send_message("🗑️ El historial de conversación de este canal ha sido vaciado.", ephemeral=True)
        await self.update_embed(interaction, self.channel_id)


# --- COG PRINCIPAL DE LA IA ---

class IACog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Comando /setia
    @app_commands.command(name="setia", description="Configura un canal por su ID para que la IA responda vía Webhook.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setia(self, interaction: discord.Interaction):
        config = get_channel_config(interaction.channel_id)
        status_text = "🟢 ACTIVO (Responde a todo)" if config["active"] and config["webhook_url"] else "🔴 INACTIVO"
        
        embed = discord.Embed(
            title="🤖 Panel de Configuración de IA por Canal",
            description="Controla el comportamiento automatizado de la IA mediante Webhooks en tiempo real.",
            color=0x2F3136
        )
        embed.add_field(name="Canal Registrado", value=f"<#{interaction.channel_id}> (`{interaction.channel_id}`)", inline=False)
        embed.add_field(name="Estado del canal", value=f"`{status_text}`", inline=True)
        embed.add_field(name="Nombre del Webhook", value=f"`{config['nombre']}`", inline=True)
        embed.add_field(name="Prompt de Personalidad", value=f"*{config['personalidad']}*", inline=False)
        
        if config["avatar_url"] and config["avatar_url"].startswith("http"):
            embed.set_thumbnail(url=config["avatar_url"])
            
        embed.set_footer(text="Autopy AI — Modo Webhook Activo")
        
        view = IAControlView(interaction.channel_id)
        await interaction.response.send_message(embed=embed, view=view)

    # Evento on_message: Escucha activa sin necesidad de comandos ni triggers
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Buscamos la configuración directamente usando el ID de este canal
        config = get_channel_config(message.channel.id)

        # Si el canal actual está configurado como activo y tiene Webhook
        if config["active"] and config["webhook_url"]:
            
            messages_payload = [{"role": "system", "content": config["personalidad"]}]
            
            for msg in config["historial"]:
                messages_payload.append(msg)
                
            messages_payload.append({"role": "user", "content": f"{message.author.name}: {message.content}"})

            async with message.channel.typing():
                headers = {
                    "Authorization": f"Bearer {AUTOPY_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "messages": messages_payload,
                    "model": "llama-3.3-70b-versatile"
                }

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(AUTOPY_BASE_URL, headers=headers, json=payload) as response:
                            if response.status == 200:
                                data = await response.json()
                                ai_response = data.get("text", "...")
                                
                                # Guardar en memoria local
                                config["historial"].append({"role": "user", "content": f"{message.author.name}: {message.content}"})
                                config["historial"].append({"role": "assistant", "content": ai_response})
                                
                                if len(config["historial"]) > 14:
                                    config["historial"] = config["historial"][-14:]

                                # --- ENVIAR RESPUESTA MEDIANTE EL WEBHOOK ---
                                async with session.post(
                                    config["webhook_url"],
                                    json={
                                        "content": ai_response,
                                        "username": config["nombre"],
                                        "avatar_url": config["avatar_url"]
                                    }
                                ) as wh_response:
                                    if wh_response.status not in [200, 204]:
                                        print(f"[Error Webhook]: Status {wh_response.status}")
                            else:
                                print(f"[Error Autopy]: Status {response.status}")
                except Exception as e:
                    print(f"[Excepción en IA]: {e}")

# Registro del Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(IACog(bot))