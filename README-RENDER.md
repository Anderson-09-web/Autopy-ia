# 🚀 Guía completa de despliegue en Render

Este proyecto se despliega en **dos servicios** + **una base de datos**:

| Servicio | Tipo | URL final |
|---|---|---|
| `autopy-api` | Web Service (Python) | `https://autopy-api.onrender.com` |
| `autopy-web` | Static Site (React) | `https://autopy-web.onrender.com` |
| `autopy-db` | PostgreSQL | (interna, solo el backend la usa) |

---

## PASO 1 — Sube el código a GitHub

```bash
# Si aún no tienes repositorio en GitHub:
git init
git remote add origin https://github.com/TU-USUARIO/autopy-ai.git
git branch -M main
git push -u origin main

# Si ya tienes el repo, solo haz push:
git add -A
git commit -m "deploy to render"
git push
```

---

## PASO 2 — Crear el servicio Backend (autopy-api)

Ve a [render.com](https://render.com) → **New +** → **Web Service**

### Conexión al repo
| Campo | Valor |
|---|---|
| **Repository** | `github.com/TU-USUARIO/autopy-ai` |
| **Branch** | `main` |

### Configuración del servicio
| Campo | Valor |
|---|---|
| **Name** | `autopy-api` |
| **Region** | Oregon (o la más cercana a tus usuarios) |
| **Runtime** | `Python 3` |
| **Root Directory** | `artifacts/api-server` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2` |
| **Instance Type** | Free (o Starter $7/mes para producción) |

### Variables de entorno — Backend
Haz click en **"Add Environment Variable"** y agrega estas una por una:

| Key | Value | Notas |
|---|---|---|
| `OPENAI_API_KEY` | `sk-...` | Tu clave de OpenAI |
| `GROQ_API_KEY` | `gsk_...` | Tu clave de Groq |
| `ADMIN_KEY` | string aleatorio seguro | Genera uno: `openssl rand -hex 32` |
| `DATABASE_URL` | *(ver Paso 3)* | Se pega después de crear la DB |

Click **"Create Web Service"** y espera a que el deploy termine (~3 min).

Cuando termine, copia tu URL: `https://autopy-api.onrender.com`

### Verificar que el backend funciona
Abre en el navegador:
```
https://autopy-api.onrender.com/api/healthz
```
Debe devolver:
```json
{"status": "ok"}
```

---

## PASO 3 — Crear la base de datos (PostgreSQL)

Ve a [render.com](https://render.com) → **New +** → **PostgreSQL**

| Campo | Valor |
|---|---|
| **Name** | `autopy-db` |
| **Region** | `Oregon` (igual que el backend) |
| **PostgreSQL Version** | `16` |
| **Instance Type** | Free |

Click **"Create Database"**.

Cuando se cree, ve a la página de la base de datos y copia el valor de **"Internal Database URL"** (empieza con `postgresql://...`).

Ahora ve al servicio `autopy-api` → **Environment** → agrega:

| Key | Value |
|---|---|
| `DATABASE_URL` | `postgresql://...` (el Internal URL que copiaste) |

Guarda y el servicio se redesplegará automáticamente.

---

## PASO 4 — Crear el servicio Frontend (autopy-web)

Ve a [render.com](https://render.com) → **New +** → **Static Site**

### Conexión al repo
| Campo | Valor |
|---|---|
| **Repository** | `github.com/TU-USUARIO/autopy-ai` |
| **Branch** | `main` |

### Configuración del servicio
| Campo | Valor |
|---|---|
| **Name** | `autopy-web` |
| **Root Directory** | *(dejar vacío — usa la raíz del repo)* |
| **Build Command** | `npm install -g pnpm@latest && pnpm install && pnpm --filter @workspace/web run build` |
| **Publish Directory** | `artifacts/web/dist/public` |

### Variables de entorno — Frontend
| Key | Value | Notas |
|---|---|---|
| `VITE_API_URL` | `https://autopy-api.onrender.com` | URL exacta del backend (sin `/` al final) |

Click **"Create Static Site"** y espera a que el build termine (~2 min).

---

## PASO 5 — Verificar todo

1. **Backend**: `https://autopy-api.onrender.com/api/v1/status` → debe mostrar modelos activos
2. **Frontend**: `https://autopy-web.onrender.com` → debe abrir la app
3. **Playground**: entra al Playground, escribe un mensaje → debe responder la IA
4. **Imágenes**: pide generar una imagen → debe devolver la URL de la imagen

---

## Variables de entorno — Resumen completo

### Backend (`autopy-api`)
| Variable | Requerida | Descripción |
|---|---|---|
| `OPENAI_API_KEY` | ✅ Sí | Clave API de OpenAI |
| `GROQ_API_KEY` | ✅ Sí | Clave API de Groq |
| `ADMIN_KEY` | ✅ Sí | Contraseña del panel admin (inventa una segura) |
| `DATABASE_URL` | ✅ Sí | URL interna de PostgreSQL (Render la da) |
| `REDIS_URL` | ❌ Opcional | Si tienes Redis; sin él usa cache en memoria |

### Frontend (`autopy-web`)
| Variable | Requerida | Descripción |
|---|---|---|
| `VITE_API_URL` | ✅ Sí | URL completa del backend, ej: `https://autopy-api.onrender.com` |

---

## Deploys automáticos

Render redespliega automáticamente cada vez que haces `git push` a `main`.

- **Backend**: redeploy tarda ~2 min
- **Frontend**: rebuild + redeploy tarda ~2 min

Si no quieres autodeploy, ve al servicio → **Settings** → desactiva **"Auto-Deploy"**.

---

## ⚠️ Limitaciones del plan gratuito

| Limitación | Free | Starter ($7/mes) |
|---|---|---|
| **Sleep tras inactividad** | Sí (15 min) | No |
| **Primera petición fría** | ~30 seg | Instantáneo |
| **Base de datos** | 1 GB, expira en 90 días | Persistente |
| **Ancho de banda** | 100 GB/mes | 100 GB/mes |

Para producción real se recomienda al menos el plan **Starter** en el backend.

---

## Solución de problemas

### El backend da error 500
- Revisa los logs en Render → `autopy-api` → **Logs**
- Verifica que `OPENAI_API_KEY`, `GROQ_API_KEY` y `DATABASE_URL` estén correctas

### El frontend muestra "Error de conexión"
- Verifica que `VITE_API_URL` apunte exactamente a tu backend (sin `/` al final)
- Reconstruye el frontend: Render → `autopy-web` → **Manual Deploy**

### Error de CORS
- El backend ya tiene `allow_origins=["*"]` en `main.py` — no requiere configuración extra

### La imagen no se genera
- El sistema intenta DALL-E 3 primero, luego DALL-E 2 como fallback
- Verifica que tu `OPENAI_API_KEY` tenga créditos en [platform.openai.com/usage](https://platform.openai.com/usage)
