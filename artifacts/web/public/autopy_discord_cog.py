"""
autopy_discord_cog.py — Cog de Discord para Autopy AI
======================================================
Integra Autopy AI en tu bot de Discord con respuestas directas al canal,
historial de conversación, identidad personalizable, generación de imágenes
y failover automático entre proveedores.

Instalación:
  pip install discord.py aiohttp

Uso:
  Copia este archivo a tu carpeta de cogs y cárgalo con:
    await bot.load_extension("autopy_discord_cog")

Comandos:
  /setia    — Activa el canal actual para respuesta automática y personaliza la identidad.
  /ia       — Consulta directa a la IA en cualquier canal.
  /iaimagen — Genera una imagen con IA a partir de una descripción.

En el canal activado con /setia, el bot detecta automáticamente si el mensaje
pide una imagen y responde en consecuencia, sin webhooks.

Documentación completa: https://autopy-ia-6a0f.onrender.com/docs
"""

import asyncio
import base64
import io
import re
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# ─── Configuración ────────────────────────────────────────────────────────────

AUTOPY_API_KEY  = "apt_..."                                      # Tu API key de Autopy
AUTOPY_BASE_URL = "https://autopy-ia-6a0f.onrender.com/api/v1"  # URL base de la API

# Modelo de chat por defecto
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Personalidad por defecto — divertida y expresiva
DEFAULT_PERSONALITY = (
    "Eres un asistente súper divertido, expresivo y carismático. "
    "Usas emojis con frecuencia, tienes mucha energía y haces comentarios ingeniosos. "
    "Eres útil pero siempre con un toque de humor. "
    "Respondes de forma concisa y directa, sin rollos innecesarios."
)

# Máximo de mensajes en el historial por canal
MAX_HISTORY = 20

# Timeouts en segundos
REQUEST_TIMEOUT = 30
IMAGE_TIMEOUT   = 90

# Palabras clave para detectar peticiones de imagen
_IMAGE_ACTION = re.compile(
    r"\b(crea|crear|genera|generar|hazme|haz|dibuja|dibujar|diseña|diseñar|pinta|pintar|"
    r"make|create|generate|draw|render)\b",
    re.IGNORECASE,
)
_IMAGE_SUBJECT = re.compile(
    r"\b(imagen|foto|fotografía|ilustración|dibujo|picture|image|arte|art|"
    r"meme|logo|portada|banner|wallpaper|avatar|icon)\b",
    re.IGNORECASE,
)


def _is_image_request(text: str) -> bool:
    """Detecta si el mensaje pide generar una imagen."""
    return bool(_IMAGE_ACTION.search(text) and _IMAGE_SUBJECT.search(text))


# ─── Base de datos en memoria ─────────────────────────────────────────────────

ia_channels: dict[int, dict] = {}


def get_channel_config(channel_id: int) -> dict:
    if channel_id not in ia_channels:
        ia_channels[channel_id] = {
            "active":       False,
            "nombre":       "Autopy AI",
            "personalidad": DEFAULT_PERSONALITY,
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
    """Llama a POST /api/v1/chat y devuelve (texto, metadata)."""
    headers = {
        "Authorization": f"Bearer {AUTOPY_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {"messages": messages, "model": model, "max_tokens": max_tokens}
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    last_error = ""

    for attempt in range(retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{AUTOPY_BASE_URL}/chat", headers=headers, json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        meta = {
                            "model":         data.get("model", model),
                            "provider":      data.get("provider", "—"),
                            "latencyMs":     data.get("latencyMs"),
                            "failoverCount": data.get("failoverCount", 0),
                            "cached":        data.get("cached", False),
                        }
                        return data.get("text", "").strip(), meta
                    elif resp.status == 401:
                        raise ValueError("❌ API key inválida o vencida. Actualiza `AUTOPY_API_KEY`.")
                    elif resp.status == 403:
                        raise ValueError("⚠️ Mensaje bloqueado por moderación de contenido.")
                    elif resp.status == 429:
                        raise ValueError("⏳ Rate limit alcanzado. Espera un momento.")
                    elif resp.status >= 500:
                        last_error = f"HTTP {resp.status}: {(await resp.text())[:200]}"
                        if attempt < retries:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        raise RuntimeError(f"Error del servidor: {last_error}")
                    else:
                        body = await resp.json(content_type=None)
                        raise ValueError(body.get("error", f"Error HTTP {resp.status}"))

        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
            last_error = str(e)
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"No se pudo conectar con Autopy AI tras {retries + 1} intentos.")

    raise RuntimeError(last_error or "Error desconocido.")


# ─── Cliente de Autopy AI — Imágenes ─────────────────────────────────────────

async def call_autopy_image(
    prompt: str,
    size: str = "1024x1024",
    retries: int = 1,
) -> tuple[Optional[str], Optional[str], dict]:
    """Llama a POST /api/v1/images y devuelve (url, base64_data, metadata)."""
    headers = {
        "Authorization": f"Bearer {AUTOPY_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {"prompt": prompt, "size": size, "format": "url"}
    timeout = aiohttp.ClientTimeout(total=IMAGE_TIMEOUT)

    for attempt in range(retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{AUTOPY_BASE_URL}/images", headers=headers, json=payload
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
                        raise RuntimeError(f"Error HTTP {resp.status}: {(await resp.text())[:200]}")

        except (aiohttp.ClientConnectorError, asyncio.TimeoutError):
            if attempt < retries:
                await asyncio.sleep(2)
                continue
            raise RuntimeError("No se pudo generar la imagen. Intenta de nuevo.")

    raise RuntimeError("Error desconocido al generar imagen.")


# ─── Modal — Editar identidad ─────────────────────────────────────────────────

class EditIdentityModal(discord.ui.Modal, title="Editar Identidad de la IA"):
    name_input = discord.ui.TextInput(
        label="Nombre de la IA",
        placeholder="Ej. Jarvis",
        max_length=50,
        required=True,
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
        self.personality_input.default = cfg["personalidad"]

    async def on_submit(self, interaction: discord.Interaction):
        cfg = get_channel_config(self.channel_id)
        cfg["nombre"]      = self.name_input.value.strip()
        cfg["personalidad"] = self.personality_input.value.strip()
        await interaction.response.send_message("✅ Identidad actualizada.", ephemeral=True)
        await self.refresh_cb(interaction, self.channel_id)


# ─── Panel de control /setia ──────────────────────────────────────────────────

class IAControlView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    def build_embed(self, channel_id: int) -> discord.Embed:
        cfg = get_channel_config(channel_id)
        estado = "🟢 ACTIVO — responde a todos los mensajes" if cfg["active"] else "🔴 INACTIVO"

        embed = discord.Embed(
            title="🤖 Panel de Configuración — Autopy AI",
            description=(
                "El bot responde directamente en este canal — sin webhooks, sin demoras extra.\n"
                "Detecta texto e imágenes de forma automática."
            ),
            color=0x7C3AED,
        )
        embed.add_field(name="Canal",        value=f"<#{channel_id}>",              inline=True)
        embed.add_field(name="Estado",       value=f"`{estado}`",                   inline=True)
        embed.add_field(name="Nombre",       value=f"`{cfg['nombre']}`",            inline=True)
        embed.add_field(name="Personalidad", value=f"*{cfg['personalidad'][:220]}*", inline=False)
        if cfg.get("last_error"):
            embed.add_field(name="⚠️ Último error", value=cfg["last_error"][:200], inline=False)
        embed.set_footer(text="Autopy AI · Groq + Gemini")
        return embed

    async def refresh(self, interaction: discord.Interaction, channel_id: int):
        self.channel_id = channel_id
        await interaction.message.edit(embed=self.build_embed(channel_id), view=self)

    @discord.ui.button(label="Editar Identidad", style=discord.ButtonStyle.primary, emoji="🎭", row=0)
    async def edit_identity(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(EditIdentityModal(self.channel_id, self.refresh))

    @discord.ui.button(label="Activar / Desactivar", style=discord.ButtonStyle.secondary, emoji="⏸️", row=0)
    async def toggle(self, interaction: discord.Interaction, _: discord.ui.Button):
        cfg = get_channel_config(self.channel_id)
        cfg["active"] = not cfg["active"]
        estado = "activada ✅" if cfg["active"] else "desactivada ⏸️"
        await interaction.response.send_message(f"IA {estado} en <#{self.channel_id}>.", ephemeral=True)
        await self.refresh(interaction, self.channel_id)

    @discord.ui.button(label="Limpiar historial", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
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

    @app_commands.command(
        name="setia",
        description="Activa el canal actual para respuesta automática y personaliza la identidad de la IA.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setia(self, interaction: discord.Interaction):
        cid = interaction.channel_id
        # Activa el canal automáticamente al usar el comando
        cfg = get_channel_config(cid)
        cfg["active"] = True
        view = IAControlView(cid)
        await interaction.response.send_message(embed=view.build_embed(cid), view=view)

    # ── /ia ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="ia", description="Pregúntale algo a la IA directamente.")
    @app_commands.describe(pregunta="¿Qué quieres preguntarle?")
    async def ia(self, interaction: discord.Interaction, pregunta: str):
        await interaction.response.send_message("💬 Generando respuesta...")

        cfg = get_channel_config(interaction.channel_id)
        messages = [
            {"role": "system", "content": cfg["personalidad"]},
            {"role": "user",   "content": f"{interaction.user.display_name}: {pregunta}"},
        ]

        try:
            text, meta = await call_autopy(messages, model=cfg["modelo"])
            info = f"· {meta['provider']} / {meta['model']}"
            if meta.get("latencyMs"):
                info += f" · {meta['latencyMs']}ms"
            await interaction.edit_original_response(
                content=(
                    f"**{interaction.user.mention} preguntó:** {pregunta}\n\n"
                    f"{text}\n\n"
                    f"-# Autopy AI {info}"
                )
            )
        except Exception as e:
            await interaction.edit_original_response(content=f"⚠️ {e}")

    # ── /iaimagen ────────────────────────────────────────────────────────────

    @app_commands.command(name="iaimagen", description="Genera una imagen con IA a partir de una descripción.")
    @app_commands.describe(prompt="Describe la imagen que quieres generar.")
    async def iaimagen(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.send_message("🎨 Generando imagen...")

        try:
            url, b64_data, meta = await call_autopy_image(prompt)
            info = f"· {meta['provider']} / {meta['model']}"
            if meta.get("latencyMs"):
                info += f" · {meta['latencyMs']}ms"
            caption = f"**Prompt:** {prompt}\n-# Autopy AI {info}"

            if url and url.startswith("http"):
                embed = discord.Embed(description=f"**Prompt:** {prompt}", color=0x7C3AED)
                embed.set_image(url=url)
                embed.set_footer(text=f"Autopy AI {info}")
                await interaction.edit_original_response(content="", embed=embed)
            elif b64_data:
                image_bytes = base64.b64decode(b64_data)
                file = discord.File(fp=io.BytesIO(image_bytes), filename="imagen.png")
                await interaction.edit_original_response(content=caption, attachments=[file])
            else:
                await interaction.edit_original_response(
                    content="⚠️ No se recibió imagen del servidor. Intenta de nuevo."
                )
        except Exception as e:
            await interaction.edit_original_response(content=f"⚠️ {e}")

    # ── Escucha pasiva — responde directo al canal, sin webhooks ──

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignorar bots y DMs
        if message.author.bot or not message.guild:
            return

        cfg = get_channel_config(message.channel.id)

        # Solo actuar en el canal activado con /setia
        if not cfg["active"]:
            return

        if _is_image_request(message.content):
            await self._handle_image_auto(message, cfg)
        else:
            await self._handle_chat_auto(message, cfg)

    async def _handle_chat_auto(self, message: discord.Message, cfg: dict):
        """Responde con texto directo al canal."""
        status = await message.channel.send("💬 Generando respuesta...")

        messages_payload = [{"role": "system", "content": cfg["personalidad"]}]
        for msg in cfg["historial"]:
            messages_payload.append(msg)
        messages_payload.append({
            "role":    "user",
            "content": f"{message.author.display_name}: {message.content}",
        })

        try:
            text, meta = await call_autopy(messages_payload, model=cfg["modelo"])
        except Exception as e:
            cfg["last_error"] = str(e)[:200]
            await status.edit(content=f"⚠️ {e}")
            return

        # Actualizar historial
        cfg["historial"].append({"role": "user",      "content": f"{message.author.display_name}: {message.content}"})
        cfg["historial"].append({"role": "assistant", "content": text})
        if len(cfg["historial"]) > MAX_HISTORY:
            cfg["historial"] = cfg["historial"][-MAX_HISTORY:]
        cfg["last_error"] = None

        # Editar el mensaje de estado con la respuesta final
        info = f"· {meta['provider']} / {meta['model']}"
        if meta.get("latencyMs"):
            info += f" · {meta['latencyMs']}ms"
        await status.edit(content=f"{text}\n\n-# Autopy AI {info}")

    async def _handle_image_auto(self, message: discord.Message, cfg: dict):
        """Genera y envía una imagen directo al canal."""
        status = await message.channel.send("🎨 Generando imagen...")

        try:
            url, b64_data, meta = await call_autopy_image(message.content)
        except Exception as e:
            cfg["last_error"] = str(e)[:200]
            await status.edit(content=f"⚠️ {e}")
            return

        cfg["last_error"] = None
        info = f"· {meta['provider']} / {meta['model']}"
        if meta.get("latencyMs"):
            info += f" · {meta['latencyMs']}ms"

        if url and url.startswith("http"):
            embed = discord.Embed(description=f"**Prompt:** {message.content}", color=0x7C3AED)
            embed.set_image(url=url)
            embed.set_footer(text=f"Autopy AI {info}")
            await status.edit(content="", embed=embed)
        elif b64_data:
            image_bytes = base64.b64decode(b64_data)
            file = discord.File(fp=io.BytesIO(image_bytes), filename="imagen.png")
            caption = f"**Prompt:** {message.content}\n-# Autopy AI {info}"
            # Eliminar el mensaje de estado y enviar con archivo adjunto
            await status.delete()
            await message.channel.send(content=caption, file=file)
        else:
            await status.edit(content="⚠️ No se pudo generar la imagen. Intenta de nuevo.")


# ─── Registro del Cog ─────────────────────────────────────────────────────────

async def setup(bot: commands.Bot):
    await bot.add_cog(IACog(bot))
