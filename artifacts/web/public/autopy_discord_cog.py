"""
autopy_discord_cog.py — Cog de Discord para Autopy AI
======================================================
Integra Autopy AI en tu bot de Discord con soporte de Webhooks,
historial de conversación por canal, identidad personalizable,
generación de imágenes y failover automático entre proveedores.

Instalación:
  pip install discord.py aiohttp

Uso:
  Copia este archivo a tu carpeta de cogs y cárgalo con:
    await bot.load_extension("autopy_discord_cog")

Comandos:
  /setia     — Configura un canal para responder a todos los mensajes
  /ia        — Consulta directa a la IA (muestra "Generando respuesta...")
  /iaimagen  — Genera una imagen con IA (muestra "Creando imagen...")
  /iamodelo  — Cambia el modelo de IA del canal

Documentación completa: https://autopy-ia-6a0f.onrender.com/docs
"""

import asyncio
import base64
import io
import re
import time
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# ─── Configuración ────────────────────────────────────────────────────────────

AUTOPY_API_KEY  = "apt_..."                                      # Tu API key de Autopy
AUTOPY_BASE_URL = "https://autopy-ia-6a0f.onrender.com/api/v1"  # URL base de la API

# Modelo por defecto. Opciones disponibles:
#   "llama-3.1-8b-instant"    → Llama 3.1 8B (Groq) — ultrarrápido
#   "llama-3.3-70b-versatile" → Llama 3.3 70B (Groq) — rápido y potente
#   "gemini-2.5-flash"        → Gemini 2.5 Flash — muy rápido y capaz
#   "gemini-2.5-pro"          → Gemini 2.5 Pro — máxima calidad
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Máximo de mensajes en el historial por canal (evita prompts demasiado largos)
MAX_HISTORY = 20

# Tiempo máximo de espera por respuesta de texto (segundos)
REQUEST_TIMEOUT = 30

# Tiempo máximo de espera por generación de imagen (segundos)
IMAGE_TIMEOUT = 90

# ─── Base de datos en memoria ─────────────────────────────────────────────────

ia_channels: dict[int, dict] = {}


def get_channel_config(channel_id: int) -> dict:
    if channel_id not in ia_channels:
        ia_channels[channel_id] = {
            "active":       False,
            "webhook_url":  None,
            "nombre":       "Autopy AI",
            "avatar_url":   "https://i.imgur.com/wSTFkRM.png",
            "personalidad": "Eres un asistente útil, amigable y conciso.",
            "modelo":       DEFAULT_MODEL,
            "historial":    [],
            "last_error":   None,
        }
    return ia_channels[channel_id]


# ─── Cliente de Autopy AI — Chat ──────────────────────────────────────────────

async def call_autopy(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    retries: int = 2,
) -> tuple[str, dict]:
    """
    Llama a POST /api/v1/chat y devuelve (texto, metadata).
    Reintenta automáticamente en caso de error 5xx o timeout.
    """
    headers = {
        "Authorization": f"Bearer {AUTOPY_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "messages":   messages,
        "model":      model,
        "max_tokens": max_tokens,
    }

    last_error = ""
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    for attempt in range(retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{AUTOPY_BASE_URL}/chat",
                    headers=headers,
                    json=payload,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = data.get("text", "").strip()
                        meta = {
                            "model":         data.get("model", model),
                            "provider":      data.get("provider", "—"),
                            "latencyMs":     data.get("latencyMs"),
                            "tokensUsed":    data.get("tokensUsed"),
                            "failoverCount": data.get("failoverCount", 0),
                            "cached":        data.get("cached", False),
                        }
                        return text, meta

                    elif resp.status == 401:
                        raise ValueError("❌ API key inválida o vencida. Actualiza `AUTOPY_API_KEY`.")
                    elif resp.status == 403:
                        raise ValueError("⚠️ Mensaje bloqueado por moderación de contenido.")
                    elif resp.status == 429:
                        raise ValueError("⏳ Rate limit alcanzado. Espera un momento.")
                    elif resp.status >= 500:
                        err_body = await resp.text()
                        last_error = f"HTTP {resp.status}: {err_body[:200]}"
                        if attempt < retries:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        raise RuntimeError(f"El servidor devolvió un error: {last_error}")
                    else:
                        body = await resp.json(content_type=None)
                        raise ValueError(body.get("error", f"Error HTTP {resp.status}"))

        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
            last_error = str(e)
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)
                continue
            raise RuntimeError(
                f"No se pudo conectar con Autopy AI después de {retries + 1} intentos. "
                f"Verifica tu conexión o el estado del servidor."
            )

    raise RuntimeError(last_error or "Error desconocido al contactar la IA.")


# ─── Cliente de Autopy AI — Imágenes ─────────────────────────────────────────

async def call_autopy_image(
    prompt: str,
    size: str = "1024x1024",
    retries: int = 1,
) -> tuple[Optional[str], Optional[str], dict]:
    """
    Llama a POST /api/v1/images y devuelve (url, base64_data, metadata).
    Si el proveedor devuelve una data-URL base64, base64_data estará relleno.
    """
    headers = {
        "Authorization": f"Bearer {AUTOPY_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "prompt": prompt,
        "size":   size,
        "format": "url",
    }

    timeout = aiohttp.ClientTimeout(total=IMAGE_TIMEOUT)

    for attempt in range(retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{AUTOPY_BASE_URL}/images",
                    headers=headers,
                    json=payload,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        meta = {
                            "model":     data.get("model", "—"),
                            "provider":  data.get("provider", "—"),
                            "latencyMs": data.get("latencyMs"),
                        }
                        raw_url = data.get("url", "")
                        raw_b64 = data.get("base64")

                        # Gemini devuelve data-URLs base64 en vez de URLs externas
                        if raw_url and raw_url.startswith("data:"):
                            raw_b64 = raw_b64 or raw_url.split(",", 1)[1]
                            return None, raw_b64, meta

                        return raw_url or None, raw_b64, meta

                    elif resp.status == 401:
                        raise ValueError("❌ API key inválida.")
                    elif resp.status == 403:
                        raise ValueError("⚠️ Imagen bloqueada por moderación.")
                    elif resp.status == 429:
                        raise ValueError("⏳ Rate limit alcanzado. Espera un momento.")
                    else:
                        body = await resp.text()
                        raise RuntimeError(f"Error HTTP {resp.status}: {body[:200]}")

        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
            if attempt < retries:
                await asyncio.sleep(2)
                continue
            raise RuntimeError("No se pudo generar la imagen. Verifica la conexión e intenta de nuevo.")

    raise RuntimeError("Error desconocido al generar la imagen.")


# ─── Modales ──────────────────────────────────────────────────────────────────

class SetWebhookModal(discord.ui.Modal, title="Configurar Canal con IA"):
    channel_id_input = discord.ui.TextInput(
        label="ID del Canal de Texto",
        placeholder="Ej. 112233445566778899",
        required=True,
        max_length=25,
    )
    url_input = discord.ui.TextInput(
        label="URL del Webhook de Discord",
        placeholder="https://discord.com/api/webhooks/...",
        required=True,
    )

    def __init__(self, current_channel_id: int, refresh_cb):
        super().__init__()
        self.current_channel_id = current_channel_id
        self.refresh_cb = refresh_cb

    async def on_submit(self, interaction: discord.Interaction):
        cid_str = self.channel_id_input.value.strip()
        if not cid_str.isdigit():
            await interaction.response.send_message(
                "❌ El ID del canal debe ser solo números.", ephemeral=True
            )
            return

        wh_url = self.url_input.value.strip()
        if not re.match(r"^https://(canary\.|ptb\.)?discord\.com/api/webhooks/\d+/\S+", wh_url):
            await interaction.response.send_message(
                "❌ La URL no parece ser un Webhook de Discord válido.", ephemeral=True
            )
            return

        cid = int(cid_str)
        cfg = get_channel_config(cid)
        cfg["webhook_url"] = wh_url
        cfg["active"] = True

        await interaction.response.send_message(
            f"✅ Canal <#{cid}> configurado. La IA responderá a todos los mensajes allí.",
            ephemeral=True,
        )
        await self.refresh_cb(interaction, cid)


class EditIdentityModal(discord.ui.Modal, title="Editar Identidad de la IA"):
    name_input = discord.ui.TextInput(
        label="Nombre de la IA",
        placeholder="Ej. Jarvis",
        max_length=50,
        required=True,
    )
    avatar_input = discord.ui.TextInput(
        label="URL del Avatar (opcional)",
        placeholder="https://link-de-imagen.png",
        required=False,
    )
    personality_input = discord.ui.TextInput(
        label="Personalidad / Prompt de Sistema",
        style=discord.TextStyle.paragraph,
        placeholder="Ej. Eres un robot sarcástico que solo habla en rimas.",
        max_length=500,
        required=True,
    )

    def __init__(self, channel_id: int, refresh_cb):
        super().__init__()
        self.channel_id = channel_id
        self.refresh_cb = refresh_cb
        cfg = get_channel_config(channel_id)
        self.name_input.default        = cfg["nombre"]
        self.avatar_input.default      = cfg.get("avatar_url", "")
        self.personality_input.default = cfg["personalidad"]

    async def on_submit(self, interaction: discord.Interaction):
        cfg = get_channel_config(self.channel_id)
        cfg["nombre"] = self.name_input.value.strip()
        if self.avatar_input.value.strip():
            cfg["avatar_url"] = self.avatar_input.value.strip()
        cfg["personalidad"] = self.personality_input.value.strip()
        await interaction.response.send_message("✅ Identidad actualizada.", ephemeral=True)
        await self.refresh_cb(interaction, self.channel_id)


# ─── Panel de control ─────────────────────────────────────────────────────────

class IAControlView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    def build_embed(self, channel_id: int) -> discord.Embed:
        cfg = get_channel_config(channel_id)
        activo = cfg["active"] and cfg["webhook_url"]
        estado = "🟢 ACTIVO — responde a todos los mensajes" if activo else "🔴 INACTIVO"

        embed = discord.Embed(
            title="🤖 Panel de Configuración — Autopy AI",
            description="Controla el bot de IA por canal usando Webhooks.",
            color=0x7C3AED,
        )
        embed.add_field(name="Canal",        value=f"<#{channel_id}> (`{channel_id}`)", inline=False)
        embed.add_field(name="Estado",       value=f"`{estado}`",                       inline=True)
        embed.add_field(name="Nombre",       value=f"`{cfg['nombre']}`",                inline=True)
        embed.add_field(name="Modelo",       value=f"`{cfg['modelo']}`",                inline=True)
        embed.add_field(name="Personalidad", value=f"*{cfg['personalidad'][:200]}*",    inline=False)
        if cfg.get("last_error"):
            embed.add_field(name="⚠️ Último error", value=cfg["last_error"][:200], inline=False)
        if cfg.get("avatar_url", "").startswith("http"):
            embed.set_thumbnail(url=cfg["avatar_url"])
        embed.set_footer(text=f"Autopy AI · {AUTOPY_BASE_URL}")
        return embed

    async def refresh(self, interaction: discord.Interaction, channel_id: int):
        self.channel_id = channel_id
        await interaction.message.edit(embed=self.build_embed(channel_id), view=self)

    @discord.ui.button(label="Establecer Canal / Webhook", style=discord.ButtonStyle.success, emoji="🔗", row=0)
    async def set_webhook(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(SetWebhookModal(self.channel_id, self.refresh))

    @discord.ui.button(label="Editar Identidad", style=discord.ButtonStyle.primary, emoji="🎭", row=0)
    async def edit_identity(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(EditIdentityModal(self.channel_id, self.refresh))

    @discord.ui.button(label="Desactivar IA", style=discord.ButtonStyle.secondary, emoji="⏸️", row=1)
    async def toggle_off(self, interaction: discord.Interaction, _: discord.ui.Button):
        cfg = get_channel_config(self.channel_id)
        cfg["active"] = not cfg["active"]
        estado = "activada" if cfg["active"] else "desactivada"
        await interaction.response.send_message(f"✅ IA {estado} en <#{self.channel_id}>.", ephemeral=True)
        await self.refresh(interaction, self.channel_id)

    @discord.ui.button(label="Limpiar historial", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def clear_history(self, interaction: discord.Interaction, _: discord.ui.Button):
        get_channel_config(self.channel_id)["historial"] = []
        await interaction.response.send_message("🗑️ Historial borrado.", ephemeral=True)
        await self.refresh(interaction, self.channel_id)


# ─── Cog principal ────────────────────────────────────────────────────────────

class IACog(commands.Cog):
    """Integración de Autopy AI para bots de Discord."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /setia ──────────────────────────────────────────────────────────────

    @app_commands.command(name="setia", description="Configura Autopy AI en un canal (solo admins).")
    @app_commands.checks.has_permissions(administrator=True)
    async def setia(self, interaction: discord.Interaction):
        cid = interaction.channel_id
        view = IAControlView(cid)
        await interaction.response.send_message(
            embed=view.build_embed(cid), view=view
        )

    # ── /ia ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="ia", description="Pregúntale algo a Autopy AI directamente.")
    @app_commands.describe(pregunta="¿Qué quieres preguntarle a la IA?")
    async def ia(self, interaction: discord.Interaction, pregunta: str):
        # Muestra "Generando respuesta..." inmediatamente mientras procesa
        await interaction.response.send_message("💬 Generando respuesta...")

        cfg = get_channel_config(interaction.channel_id)
        messages = [
            {"role": "system", "content": cfg["personalidad"]},
            {"role": "user",   "content": f"{interaction.user.display_name}: {pregunta}"},
        ]

        try:
            text, meta = await call_autopy(messages, model=cfg["modelo"])
            provider_info = f"· {meta['provider']} / {meta['model']}"
            if meta.get("latencyMs"):
                provider_info += f" · {meta['latencyMs']}ms"

            await interaction.edit_original_response(
                content=(
                    f"**{interaction.user.mention} preguntó:** {pregunta}\n\n"
                    f"{text}\n\n"
                    f"-# Autopy AI {provider_info}"
                )
            )
        except Exception as e:
            await interaction.edit_original_response(content=f"⚠️ {e}")

    # ── /iaimagen ────────────────────────────────────────────────────────────

    @app_commands.command(name="iaimagen", description="Genera una imagen con IA a partir de una descripción.")
    @app_commands.describe(prompt="Describe la imagen que quieres generar.")
    async def iaimagen(self, interaction: discord.Interaction, prompt: str):
        # Muestra "Creando imagen..." inmediatamente mientras procesa
        await interaction.response.send_message("🎨 Creando imagen...")

        try:
            url, b64_data, meta = await call_autopy_image(prompt)
            provider_info = f"· {meta['provider']} / {meta['model']}"
            if meta.get("latencyMs"):
                provider_info += f" · {meta['latencyMs']}ms"

            caption = f"**Prompt:** {prompt}\n-# Autopy AI {provider_info}"

            if url and url.startswith("http"):
                # URL pública — enviamos como embed con imagen
                embed = discord.Embed(description=f"**Prompt:** {prompt}", color=0x7C3AED)
                embed.set_image(url=url)
                embed.set_footer(text=f"Autopy AI {provider_info}")
                await interaction.edit_original_response(content="", embed=embed)

            elif b64_data:
                # Imagen en base64 (Gemini) — la enviamos como archivo adjunto
                image_bytes = base64.b64decode(b64_data)
                file = discord.File(fp=io.BytesIO(image_bytes), filename="imagen.png")
                await interaction.edit_original_response(content=caption, attachments=[file])

            else:
                await interaction.edit_original_response(
                    content="⚠️ No se recibió imagen del servidor. Intenta de nuevo."
                )

        except Exception as e:
            await interaction.edit_original_response(content=f"⚠️ {e}")

    # ── /iamodelo ────────────────────────────────────────────────────────────

    @app_commands.command(name="iamodelo", description="Cambia el modelo de IA del canal actual.")
    @app_commands.describe(
        modelo=(
            "Modelo a usar: llama-3.1-8b-instant · llama-3.3-70b-versatile · "
            "gemini-2.5-flash · gemini-2.5-pro"
        )
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def iamodelo(self, interaction: discord.Interaction, modelo: str):
        cfg = get_channel_config(interaction.channel_id)
        cfg["modelo"] = modelo.strip()
        await interaction.response.send_message(
            f"✅ Modelo cambiado a `{cfg['modelo']}` para <#{interaction.channel_id}>.", ephemeral=True
        )

    # ── Escucha pasiva (responde a todos los mensajes del canal configurado) ──

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignorar bots y DMs
        if message.author.bot or not message.guild:
            return

        cfg = get_channel_config(message.channel.id)

        # Solo actuar si el canal está activo con webhook
        if not (cfg["active"] and cfg["webhook_url"]):
            return

        # Construir historial de conversación
        messages_payload = [{"role": "system", "content": cfg["personalidad"]}]
        for msg in cfg["historial"]:
            messages_payload.append(msg)
        messages_payload.append({
            "role":    "user",
            "content": f"{message.author.display_name}: {message.content}",
        })

        async with message.channel.typing():
            try:
                text, meta = await call_autopy(messages_payload, model=cfg["modelo"])
            except Exception as e:
                cfg["last_error"] = str(e)[:200]
                print(f"[Autopy AI] Error en canal {message.channel.id}: {e}")
                return

        # Actualizar historial (limitado a MAX_HISTORY mensajes)
        cfg["historial"].append({"role": "user",      "content": f"{message.author.display_name}: {message.content}"})
        cfg["historial"].append({"role": "assistant",  "content": text})
        if len(cfg["historial"]) > MAX_HISTORY:
            cfg["historial"] = cfg["historial"][-MAX_HISTORY:]
        cfg["last_error"] = None

        # Enviar por webhook con la identidad configurada
        wh_payload = {
            "content":    text,
            "username":   cfg["nombre"],
            "avatar_url": cfg["avatar_url"],
        }

        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(cfg["webhook_url"], json=wh_payload) as wh_resp:
                    if wh_resp.status not in (200, 204):
                        print(f"[Autopy AI] Error webhook {wh_resp.status} en canal {message.channel.id}")
        except Exception as e:
            print(f"[Autopy AI] Excepción enviando webhook: {e}")


# ─── Registro del Cog ─────────────────────────────────────────────────────────

async def setup(bot: commands.Bot):
    await bot.add_cog(IACog(bot))
