# SkillForge AI

AI-powered career mentor platform. Users upload a resume, share a portfolio URL, and receive a skill-gap analysis plus a personalized learning roadmap.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TanStack Router / TanStack Start, Vite, Tailwind CSS v4, shadcn/ui |
| Backend | FastAPI, Uvicorn, PyMongo, Authlib |
| Database | MongoDB Atlas |
| Auth | Google OAuth 2.0 (backend) + session cookies; client-side password auth (localStorage) |

## Project Structure

```
skillforge-ai/
├── frontend/                  # React + Vite + TanStack Start app
│   ├── src/
│   │   ├── routes/            # /, /login, /signup, /analysis, /plan
│   │   ├── components/
│   │   │   ├── auth/          # Auth layout, password input, RequireAuth guard
│   │   │   └── ui/            # shadcn/ui components
│   │   ├── lib/
│   │   │   ├── auth-store.ts  # Client-side auth (password + Google OAuth)
│   │   │   ├── mock-data.ts   # Static analysis/plan data
│   │   │   └── profile-store.ts
│   │   ├── server.ts          # TanStack Start SSR entry wrapper
│   │   ├── router.tsx
│   │   └── styles.css
│   ├── .env.example
│   ├── .env
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── backend/                   # FastAPI service
│   ├── app/
│   │   ├── main.py            # App factory, CORS, session middleware, routers
│   │   ├── config.py          # Pydantic Settings
│   │   ├── database/
│   │   │   └── mongodb.py     # PyMongo connection, indexes, collection accessors
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── resumes.py
│   │   │   ├── portfolios.py
│   │   │   ├── career_profiles.py
│   │   │   ├── learning_paths.py
│   │   │   └── progress.py
│   │   ├── services/
│   │   │   ├── google_auth.py
│   │   │   ├── resume_service.py
│   │   │   ├── portfolio_service.py
│   │   │   ├── career_service.py
│   │   │   ├── learning_service.py
│   │   │   └── progress_service.py
│   │   ├── schemas/           # Pydantic models
│   │   └── utils/
│   │       └── object_id.py
│   ├── run.py
│   ├── .env.example
│   ├── .env
│   └── requirements.txt
│
├── .gitignore
└── README.md
```

## Local Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+ (with npm)
- MongoDB Atlas cluster (or local MongoDB)

---

### Backend

```bash
cd backend
python -m venv venv
```

**Activate the virtual environment:**
- **Windows (PowerShell):** `venv\Scripts\activate`
- **macOS / Linux:** `source venv/bin/activate`

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Configure environment variables:**

Copy `.env.example` to `.env` and fill in the values. Required variables:

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | OAuth callback (default `http://localhost:8000/api/auth/google/callback`) |
| `FRONTEND_URL` | Allowed CORS origin (default `http://localhost:5173`) |
| `SESSION_SECRET` | Secret key for session cookies |
| `ENVIRONMENT` | `development` or `production` |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `MONGODB_DATABASE` | Database name (default `skillforge`) |

**Run the backend:**
```bash
python run.py
```

Backend runs at `http://localhost:8000`.

---

### Frontend

```bash
cd frontend
npm install
```

**Configure environment variables:**

Copy `.env.example` to `.env` if needed. Required variable:

| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | Backend base URL (default `http://localhost:8000`) |

**Run the frontend:**
```bash
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## API Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service status |
| GET | `/health` | Backend health |
| GET | `/api/health` | API health with database info |

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/google/login` | Redirect to Google OAuth consent screen |
| GET | `/api/auth/google/callback` | Google OAuth callback |
| GET | `/api/auth/me` | Get current authenticated user |
| POST | `/api/auth/logout` | Clear session |

### Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/users/me` | Get authenticated user profile |

### Resumes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/resumes` | Upload resume (PDF/DOCX) or raw text |
| GET | `/api/resumes` | List user's resumes |
| GET | `/api/resumes/{id}` | Get a specific resume |
| DELETE | `/api/resumes/{id}` | Delete a specific resume |

### Portfolios

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/portfolios` | Analyze portfolio URL and save |
| GET | `/api/portfolios` | List user's portfolios |
| GET | `/api/portfolios/{id}` | Get a specific portfolio |
| DELETE | `/api/portfolios/{id}` | Delete a specific portfolio |

### Career Profiles

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/career-profiles` | Generate career analysis profile |
| GET | `/api/career-profiles` | List user's career profiles |
| GET | `/api/career-profiles/{id}` | Get a specific career profile |

### Learning Paths

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/learning-paths` | Generate learning roadmap |
| GET | `/api/learning-paths` | List user's learning paths |
| GET | `/api/learning-paths/{id}` | Get a specific learning path |
| PATCH | `/api/learning-paths/{id}` | Update roadmap or duration |

### Progress

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/progress` | Get user progress (auto-initializes if missing) |
| PUT | `/api/progress` | Replace user progress |
| PATCH | `/api/progress` | Patch user progress |

---

## Database

### MongoDB Atlas Integration

The backend uses **PyMongo** (not Motor/ODM) to connect to MongoDB Atlas.

**Collections:**

| Collection | Purpose | Indexes |
|------------|---------|---------|
| `users` | Google OAuth user profiles | `email` (unique) |
| `resumes` | Uploaded resumes + parsed NER profiles | `userId` |
| `portfolios` | Portfolio URL analysis records | `userId` |
| `career_profiles` | Career analysis results | `userId` |
| `learning_paths` | Generated learning roadmaps | `userId` |
| `progress` | User progress tracking | `userId` (unique) |

Indexes are created automatically on app startup via `init_indexes()` in `app/database/mongodb.py`.

---

## Authentication & Sessions

- **Google OAuth**: Full OAuth 2.0 flow using `authlib`. Session state stored in signed cookies via Starlette `SessionMiddleware`.
- **Session cookie name**: `skillforge_session`
- **Session duration**: 14 days
- **Same-site**: `lax`; `https_only` enabled in production
- **Client-side password auth**: Email/password signup and signin are stored in `localStorage` only. There is no backend endpoint for password auth.
- **Auth guard**: Frontend `RequireAuth` component protects `/`, `/analysis`, `/plan`.

---

## AI / Analysis Components

This project does **not** call external LLM or ML APIs. Analysis and recommendations are generated using rule-based logic:

- **Resume NER**: Regex-based extraction of name, email, phone, and a curated skills catalog from PDF/DOCX text (via PyMuPDF and python-docx).
- **Portfolio Analysis**: Basic HTML scraping with BeautifulSoup plus a default skills/projects profile.
- **Career Analysis**: Heuristic skill matching against predefined role requirement catalogs. Calculates readiness scores, skill gaps, and career match rankings.
- **Learning Roadmap**: Static week-by-week curriculum templates sliced by requested `durationWeeks`.

---

## Frontend Routes

| Route | Description |
|-------|-------------|
| `/` | Home — resume upload, portfolio input, target role selection |
| `/analysis` | Career analysis — readiness score, extracted skills, skill gaps |
| `/plan` | Personalized plan — roadmap, courses, projects, certifications, interview prep |
| `/login` | Sign in (password or Google) |
| `/signup` | Create account (password or Google) |

> Note: `/analysis` and `/plan` currently display static mock data from `src/lib/mock-data.ts`. Backend-driven analysis endpoints exist but are not yet wired to these pages.

---

## Available Scripts

### Frontend (`frontend/package.json`)

| Script | Command | Purpose |
|--------|---------|---------|
| dev | `npm run dev` | Start Vite dev server on port 5173 |
| build | `npm run build` | Production build |
| build:dev | `npm run build --mode development` | Development build |
| preview | `npm run preview` | Preview production build |
| lint | `npm run lint` | ESLint |
| format | `npm run format` | Prettier |

### Backend

| Script | Command | Purpose |
|--------|---------|---------|
| run | `python run.py` | Start Uvicorn with auto-reload on port 8000 |

---

## Troubleshooting

### MongoDB Connection Fails
- Verify `MONGODB_URI` in `backend/.env` is correct and the Atlas cluster allows your IP.
- Ensure the database user has read/write permissions on the target database.

### Google OAuth Redirect Mismatch
- `GOOGLE_REDIRECT_URI` in `.env` must match the authorized redirect URI in Google Cloud Console.
- `FRONTEND_URL` must match the origin serving the frontend.

### Session Cookie Not Persisting
- Ensure `FRONTEND_URL` in the backend `.env` matches the actual frontend origin.
- Check that the browser allows third-party cookies if frontend and backend are on different origins.

### Frontend Shows Mock Data Instead of Backend Analysis
- The current `/analysis` and `/plan` routes use static mock data. Backend analysis APIs exist but are not yet integrated into these pages.

---

## Security

- **Never commit `.env` files.** They are gitignored. Use `.env.example` for documentation.
- **Rotate `SESSION_SECRET`** in production. Use a strong, random 32+ byte string.
- **Restrict MongoDB Atlas network access** to known IPs and use a dedicated database user with minimal privileges.
- **Google OAuth secrets** (`GOOGLE_CLIENT_SECRET`) must remain server-side only.
- **CORS** is configured to allow `FRONTEND_URL`, `http://localhost:5173`, and `http://127.0.0.1:5173`. Add production frontend origins before deploying.
- **Session cookies** use `same_site="lax"` and `https_only` in production.

---

## OpenAPI Documentation

FastAPI auto-generated docs are available when the backend is running:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
