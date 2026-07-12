# 🛡️ Salama — Community Safety

**Offline-first community emergency alerts, hazard map, and neighbor check-ins.**
Built for areas with poor connectivity: raise an **SOS**, share **local hazards**, and **check in** with neighbors — fast, mobile, installable to your home screen.

> Part of the *Antorm* impact suite. Repo: `antorm1/salama`

---

## ✨ Features

- **🆘 One-tap SOS** — critical alert with optional GPS location.
- **🗺️ Local hazard feed** — categorized (sos / hazard / medical / weather / crime / other) and severity-ranked (low → critical).
- **✓ Neighbor check-ins** — let your community know you're safe.
- **🔐 Auth** — bcrypt-hashed passwords, JWT sessions, seeded admin.
- **📱 Installable PWA** — works offline, adds to home screen, no app store.
- **🛡️ Secure by default** — parameterized SQL, input validation, CORS allowlist.

## 🧱 Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18 + TypeScript + Vite + TailwindCSS + vite-plugin-pwa |
| Backend | FastAPI (Python) + stdlib-sqlite3 (zero DB deps) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Storage | SQLite (`salama.db`); swap to Postgres via `DATABASE_URL` |

## 📂 Project Structure

```
salama/
├── backend/
│   ├── main.py            # FastAPI app: auth, alerts, checkins, health
│   ├── database.py        # SQLite connection, schema, admin seed
│   ├── security.py        # password hashing + JWT
│   ├── schemas.py         # Pydantic request/response models
│   ├── config.py          # settings from .env
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── vite.config.ts     # PWA config + API base
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig*.json
│   ├── public/            # icons, favicon, manifest assets
│   └── src/
│       ├── main.tsx, App.tsx, Layout.tsx
│       ├── api.ts          # typed fetch client
│       ├── useAuth.ts      # auth context
│       └── pages/         # Home, Alerts, CheckIns, Login, Register
└── README.md
```

## 🚀 Quick Start

### 1. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # or: python3 -m venv .venv
pip install -r requirements.txt
cp .env.example .env            # edit SECRET_KEY + SEED_ADMIN_PASSWORD
python main.py                  # creates DB + seeds admin, serves on :8000
```

### 2. Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```
> Point the frontend at a different API with `VITE_API_BASE=https://api.example.com npm run build`.

### 3. Production build
```bash
cd frontend && npm install && npm run build   # outputs dist/ (service-worker + manifest)
# Serve dist/ with any static host (nginx, Vercel, Fly, GitHub Pages)
```

## 🔑 Default Admin
Seeded on first run (override in `.env`):
- **username:** `admin`
- **password:** `salama-admin-pass`

## 📡 API Reference

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/health` | – | Service health |
| POST | `/auth/register` | – | Create account |
| POST | `/auth/token` | – | Login → JWT |
| GET | `/auth/me` | ✅ | Current user |
| GET | `/alerts?status=active\|resolved\|all` | ✅ | List alerts |
| POST | `/alerts` | ✅ | Create alert (incl. SOS) |
| PATCH | `/alerts/{id}` | ✅* | Resolve/reopen (*author or admin) |
| DELETE | `/alerts/{id}` | admin | Remove alert |
| GET | `/checkins?only_mine=true\|false` | ✅ | List check-ins |
| POST | `/checkins` | ✅ | Create check-in |

### Example: register & raise an SOS
```bash
curl -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"amina","phone":"+254712345678","password":"str0ngpw","display_name":"Amina"}'

TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"amina","password":"str0ngpw"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/alerts \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"category":"sos","severity":"critical","title":"SOS — need help","lat":-1.2921,"lng":36.8219}'
```

## 🔒 Security Notes
- Passwords hashed with **bcrypt**; never stored or returned in plaintext.
- All DB queries use **parameterized SQL** (no string interpolation).
- JWT secret loaded from env — **change `SECRET_KEY` before deploying**.
- CORS restricted to configured origins.

## 📄 License
MIT © Antorm
