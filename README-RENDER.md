# 🚀 Despliegue en Render — Un solo Web Service

Frontend + Backend en un único servicio. Base de datos Neon (externa).

---

## Resumen de lo que vas a crear

| Qué | Tipo en Render |
|---|---|
| Backend (FastAPI) + Frontend (React) | **Web Service** — Python |
| Base de datos | **Neon** (externa, ya la tienes) |

Un solo servicio sirve todo: las rutas `/api/*` van al backend y el resto carga el frontend React.

---

## PASO 1 — Sube el código a GitHub

```bash
# Primera vez:
git remote add origin https://github.com/TU-USUARIO/autopy-ai.git
git branch -M main
git push -u origin main

# Actualizaciones posteriores:
git add -A
git commit -m "mensaje"
git push
```

---

## PASO 2 — Crear el Web Service en Render

Ve a [render.com](https://render.com) → **New +** → **Web Service**

### 🔗 Conectar repositorio

| Campo | Valor |
|---|---|
| **Repository** | Tu repo de GitHub |
| **Branch** | `main` |

---

### ⚙️ Configuración principal

| Campo | Valor exacto |
|---|---|
| **Name** | `autopy-ai` (o el que quieras) |
| **Region** | Oregon (o la más cercana) |
| **Runtime** | `Python 3` |
| **Root Directory** | *(dejar vacío)* |
| **Instance Type** | Free (o Starter $7/mes para producción) |

---

### 🔨 Build Command

```
bash render-build.sh
```

> **¿Por qué un script?** Render tiene `/usr/lib/node_modules` como read-only, así que `npm install -g pnpm` falla con `EROFS`. El script instala pnpm en `$HOME/.npm-global` (escribible) y luego construye todo.

Lo que hace el script, en orden:
1. Instala pnpm en directorio local (`$HOME/.npm-global`)
2. Instala dependencias Node del monorepo
3. Construye el frontend React (genera `artifacts/web/dist/public/`)
4. Instala dependencias Python del backend

---

### ▶️ Start Command

```
cd artifacts/api-server && uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
```

---

### 🔑 Variables de entorno

Haz click en **"Add Environment Variable"** para cada una:

| Key | Value | Obligatoria |
|---|---|---|
| `DATABASE_URL` | `postgresql://usuario:pass@ep-xxx.neon.tech/neondb?sslmode=require` | ✅ Sí |
| `OPENAI_API_KEY` | `sk-...` | ✅ Sí |
| `GROQ_API_KEY` | `gsk_...` | ✅ Sí |
| `ADMIN_KEY` | string seguro aleatorio | ✅ Sí |

> **Dónde encuentras tu Neon URL:**
> Ve a [neon.tech](https://neon.tech) → tu proyecto → **Connection Details** → copia la **Connection string** (con `?sslmode=require` al final).

> **Generar ADMIN_KEY seguro:**
> ```bash
> openssl rand -hex 32
> ```
> O usa cualquier string largo y aleatorio.

---

### Click "Create Web Service"

El primer deploy tarda ~4-5 minutos porque instala Node, pnpm, Python y construye el frontend.

---

## PASO 3 — Verificar que funciona

Una vez desplegado, tu URL será algo como `https://autopy-ai.onrender.com`.

| Verificación | URL | Resultado esperado |
|---|---|---|
| Backend OK | `/api/healthz` | `{"status":"ok"}` |
| Modelos activos | `/api/v1/status` | JSON con modelos |
| Frontend | `/` | Carga la app |
| Docs API | `/api/docs` | Swagger UI |

---

## 📋 Resumen visual de todos los campos

```
┌─────────────────────────────────────────────────────┐
│              RENDER — NEW WEB SERVICE               │
├──────────────────────┬──────────────────────────────┤
│ Name                 │ autopy-ai                    │
│ Runtime              │ Python 3                     │
│ Branch               │ main                         │
│ Root Directory       │ (vacío)                      │
│ Build Command        │ npm install -g pnpm@latest   │
│                      │ && pnpm install              │
│                      │ && BASE_PATH=/ pnpm          │
│                      │ --filter @workspace/web      │
│                      │ run build                    │
│                      │ && pip install -r            │
│                      │ artifacts/api-server/        │
│                      │ requirements.txt             │
│ Start Command        │ cd artifacts/api-server      │
│                      │ && uvicorn main:app          │
│                      │ --host 0.0.0.0               │
│                      │ --port $PORT                 │
│                      │ --workers 2                  │
│ Health Check Path    │ /api/healthz                 │
├──────────────────────┼──────────────────────────────┤
│ DATABASE_URL         │ tu Neon connection string    │
│ OPENAI_API_KEY       │ sk-...                       │
│ GROQ_API_KEY         │ gsk_...                      │
│ ADMIN_KEY            │ string aleatorio seguro      │
└──────────────────────┴──────────────────────────────┘
```

---

## 🔄 Deploys automáticos

Cada `git push` a `main` lanza un nuevo deploy automáticamente.

---

## ⚠️ Limitaciones del plan gratuito

| | Free | Starter ($7/mes) |
|---|---|---|
| Sleep tras 15 min sin tráfico | ✅ Sí | ❌ No |
| Primera petición tras sleep | ~30 seg | Instantáneo |
| RAM | 512 MB | 512 MB |
| CPU | 0.1 | 0.5 |

**Recomendación:** usa **Starter** si el proyecto es para usuarios reales.

---

## 🛠️ Solución de problemas

### Build falla en `pnpm install`
→ Verifica que el `Root Directory` esté **vacío** (no pongas `artifacts/api-server`)

### Build falla en `pip install`
→ Verifica que el archivo `artifacts/api-server/requirements.txt` exista en tu repo

### App abre pero el chat da error
→ Verifica `OPENAI_API_KEY` y `GROQ_API_KEY` en el dashboard de Render → Environment

### Base de datos da error de conexión
→ La Neon URL debe terminar en `?sslmode=require`
→ Ejemplo correcto: `postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require`

### La imagen no se genera
→ Verifica que tu cuenta de OpenAI tenga créditos en [platform.openai.com/usage](https://platform.openai.com/usage)
→ El sistema intenta DALL-E 3 primero, luego DALL-E 2 automáticamente
