# MailMind — Setup Instructions

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Set Up .env
```bash
cp .env.example .env
# Fill in your values in .env
```

## 3. Add credentials.json
- Download from Google Cloud Console
- Place in project root (next to manage.py)

## 4. Run Migrations (for sessions)
```bash
python manage.py migrate
```

## 5. Create Sessions Folder
```bash
mkdir sessions
```

## 6. Run Server
```bash
python manage.py runserver
```

## API Endpoints

| Method | URL | Purpose |
|--------|-----|---------|
| GET  | /auth/login/              | Get Google OAuth URL |
| GET  | /auth/callback/           | Google redirects here |
| POST | /auth/profile/            | Save Name + Roll No |
| GET  | /auth/me/                 | Check login status |
| POST | /auth/logout/             | Logout |
| POST | /api/emails/preferences/  | Save preferences → Gemini maps them |
| GET  | /api/emails/preferences/get/ | Get saved preferences |
| POST | /api/emails/fetch/        | Fetch + classify all emails |
| GET  | /api/emails/              | Get classified emails |
| GET  | /api/emails/search/?q=X   | Search emails |
| GET  | /api/notifications/       | Get unseen notifications |
| POST | /api/notifications/seen/  | Mark notifications seen |

## File Structure
```
mailmind/
  .env                    ← your keys (never commit)
  .env.example            ← template
  .gitignore
  credentials.json        ← from Google Cloud (never commit)
  college_data.py         ← IITJ clubs + fests brain
  manage.py
  requirements.txt

  mailmind/
    settings.py
    urls.py
    wsgi.py

  emails/
    models.py             ← MongoDB collections
    gmail_service.py      ← fetch emails
    gemini_service.py     ← AI classifier
    calendar_service.py   ← create calendar events
    views.py              ← API endpoints
    urls.py               ← routes

  users/
    views.py              ← OAuth login
    urls.py               ← auth routes

  sessions/               ← Django session files
```
