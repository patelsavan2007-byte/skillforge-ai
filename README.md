# SKILLFORGE AI

SkillForge AI is an AI-powered career mentor application for students and professionals.

## Project Structure

```
skillforge-ai/
│
├── frontend/             # React + Vite + TanStack Router UI
│   ├── public/
│   ├── src/
│   ├── .env
│   ├── .env.example
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── backend/              # FastAPI Google OAuth Authentication Backend
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── services/
│   │   └── routes/
│   ├── run.py
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
│
├── .gitignore
└── README.md
```

## Local Development Setup

### Backend (Google OAuth Authentication)

1. Open a terminal and navigate to `backend`:

```bash
cd backend
```

2. Create and activate a virtual environment:

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Verify `.env` configuration (Google OAuth Client ID & Secret).

5. Start the backend server:

```bash
python run.py
```

> The backend will start at `http://localhost:8000`. OpenAPI docs are available at `http://localhost:8000/docs`.

---

### Frontend (SkillForge AI Web App)

1. Open a second terminal and navigate to `frontend`:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

> The application will run at `http://localhost:5173`.
