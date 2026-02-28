# MailMind Backend — Team CODEX

## What's Fixed

| Bug | Location | Fix |
|-----|----------|-----|
| Missing `return` in OAuth callback | `users/views.py:callback()` | Added `return HttpResponseRedirect(...)` — without this, Django served a blank 500 |
| `auth_required` decorator lost function names | `emails/views.py` | Added `@functools.wraps(view_func)` to preserve metadata |
| Calendar events never stored in MongoDB | `emails/views.py` | Added `save_calendar_event()` call after Google Calendar API success |
| No calendar API endpoint | `emails/urls.py` | Added `GET /api/emails/calendar/` and `POST /api/emails/calendar/add/` |
| No `save_calendar_event` / `get_calendar_events` in models | `emails/models.py` | Added both functions + `calendar_events` collection |
| CORS missing port 3000 | `mailmind/settings.py` | Added `localhost:3000` to `CORS_ALLOWED_ORIGINS` |
| FRONTEND_URL not in settings/env | `mailmind/settings.py` | Added `FRONTEND_URL` setting |
| No sessions directory auto-creation | `mailmind/settings.py` | Added `os.makedirs(...)` |

## APIs Required

### You Must Create Accounts/Keys For:

1. **Google Cloud Console** — `console.cloud.google.com`
   - Create OAuth 2.0 credentials
   - Enable: Gmail API, Google Calendar API, Google People API
   - Download `credentials.json` → place in `/backend/` root
   - Add Redirect URI: `http://localhost:8000/auth/callback/`

2. **Gemini AI** — `aistudio.google.com/app/apikey`
   - Free tier works fine for dev
   - Set as `GEMINI_API_KEY` in `.env`

3. **MongoDB Atlas** — `cloud.mongodb.com` (free tier)
   - Or use local: `mongodb://localhost:27017/`
   - Set as `MONGO_URI` in `.env`

## Setup

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Copy and fill env
cp .env.example .env
# Edit .env with your real keys

# 3. Run migrations (for Django sessions)
python manage.py migrate

# 4. Seed sample data (optional — for testing without real Gmail)
python seed_db.py

# 5. Start server
python manage.py runserver
```

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET    | `/auth/login/` | Returns Google OAuth URL |
| GET    | `/auth/callback/` | OAuth callback from Google |
| POST   | `/auth/profile/` | Save name + roll number |
| GET    | `/auth/me/` | Get current user info |
| GET    | `/auth/logout/` | Logout |
| POST   | `/api/emails/preferences/` | Save user interests |
| GET    | `/api/emails/preferences/get/` | Get saved preferences |
| POST   | `/api/emails/fetch/` | Fetch + classify Gmail emails |
| GET    | `/api/emails/` | Get all classified emails |
| GET    | `/api/emails/search/?q=RAID` | Search emails |
| GET    | `/api/emails/calendar/` | **NEW** Get calendar events |
| POST   | `/api/emails/calendar/add/` | **NEW** Add manual event |
| GET    | `/api/emails/notifications/` | Get unread notifications |
| POST   | `/api/emails/notifications/seen/` | Mark all seen |
| POST   | `/api/debug/login/` | **DEV ONLY** Login as seeded test user |

## MongoDB Collections

- `users` — Google OAuth profiles
- `preferences` — User interest weights (Gemini Model 1 output)
- `emails` — Raw + classified Gmail messages
- `calendar_events` — Events for the calendar dashboard **(NEW)**
- `notifications` — Q1-priority push alerts
