# FlavorVault

A modern recipe management and sharing platform built with Python, FastAPI, and SQLAlchemy.

## Features

- **User Authentication** — Secure registration and login with JWT-based authentication and bcrypt password hashing
- **Recipe Management** — Full CRUD operations for creating, reading, updating, and deleting recipes
- **Ingredient Tracking** — Associate ingredients with recipes including quantities and units
- **Recipe Categories** — Organize recipes by categories and tags for easy discovery
- **Search & Filter** — Search recipes by name, ingredients, category, or tags
- **User Profiles** — Personalized user profiles with saved/favorited recipes
- **Rating & Reviews** — Rate and review recipes from other users
- **Async API** — Fully asynchronous API endpoints for high performance

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI
- **Database:** SQLite (via aiosqlite for async) / PostgreSQL (production)
- **ORM:** SQLAlchemy 2.0 (async)
- **Authentication:** JWT (python-jose) + bcrypt
- **Validation:** Pydantic v2
- **Templates:** Jinja2 + Tailwind CSS
- **Testing:** pytest + pytest-asyncio + httpx

## Folder Structure

```
flavorvault/
├── app/
│   ├── core/
│   │   ├── config.py          # Application settings (BaseSettings)
│   │   ├── database.py        # Async SQLAlchemy engine & session
│   │   ├── security.py        # JWT token & password hashing utilities
│   │   └── __init__.py
│   ├── models/
│   │   ├── user.py            # User model
│   │   ├── recipe.py          # Recipe model
│   │   ├── category.py        # Category model
│   │   ├── ingredient.py      # Ingredient model
│   │   ├── review.py          # Review/Rating model
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── user.py            # User request/response schemas
│   │   ├── recipe.py          # Recipe request/response schemas
│   │   ├── category.py        # Category schemas
│   │   ├── ingredient.py      # Ingredient schemas
│   │   ├── review.py          # Review schemas
│   │   └── __init__.py
│   ├── services/
│   │   ├── user.py            # User business logic
│   │   ├── recipe.py          # Recipe business logic
│   │   ├── category.py        # Category business logic
│   │   ├── review.py          # Review business logic
│   │   └── __init__.py
│   ├── routers/
│   │   ├── auth.py            # Authentication routes
│   │   ├── users.py           # User routes
│   │   ├── recipes.py         # Recipe routes
│   │   ├── categories.py      # Category routes
│   │   ├── reviews.py         # Review routes
│   │   └── __init__.py
│   ├── dependencies/
│   │   ├── auth.py            # Auth dependency (get_current_user)
│   │   └── __init__.py
│   ├── templates/             # Jinja2 HTML templates
│   │   ├── base.html
│   │   └── ...
│   └── main.py                # FastAPI application entry point
├── tests/
│   ├── test_auth.py
│   ├── test_recipes.py
│   ├── test_users.py
│   └── conftest.py
├── .env                       # Environment variables (not committed)
├── .env.example               # Example environment variables
├── requirements.txt           # Python dependencies
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd flavorvault
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and update values:

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./flavorvault.db` |
| `SECRET_KEY` | JWT signing secret (use a strong random string) | `your-secret-key-change-in-production` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time in minutes | `30` |
| `ENVIRONMENT` | Runtime environment | `development` |

### 5. Initialize the Database

The database tables are created automatically on application startup via the lifespan handler. To seed initial data (if a seed script is provided):

```bash
python -m app.seed
```

### 6. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

Interactive API documentation is available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### 7. Run Tests

```bash
pytest -v
```

## Deployment

### Vercel Deployment

1. Install the Vercel CLI:

```bash
npm install -g vercel
```

2. Create a `vercel.json` in the project root:

```json
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

3. Set environment variables in the Vercel dashboard under **Settings → Environment Variables**. Use a PostgreSQL connection string (e.g., from Neon, Supabase, or Railway) for `DATABASE_URL` in production.

4. Deploy:

```bash
vercel --prod
```

### Docker Deployment (Alternative)

```bash
docker build -t flavorvault .
docker run -p 8000:8000 --env-file .env flavorvault
```

## API Routes Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and receive JWT token |

### Users

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/me` | Get current user profile |
| `PUT` | `/users/me` | Update current user profile |

### Recipes

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/recipes` | List all recipes (with search/filter) |
| `POST` | `/recipes` | Create a new recipe |
| `GET` | `/recipes/{id}` | Get recipe details |
| `PUT` | `/recipes/{id}` | Update a recipe |
| `DELETE` | `/recipes/{id}` | Delete a recipe |

### Categories

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/categories` | List all categories |
| `POST` | `/categories` | Create a new category |
| `GET` | `/categories/{id}` | Get category with recipes |

### Reviews

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/recipes/{id}/reviews` | List reviews for a recipe |
| `POST` | `/recipes/{id}/reviews` | Add a review to a recipe |
| `PUT` | `/reviews/{id}` | Update a review |
| `DELETE` | `/reviews/{id}` | Delete a review |

## License

Private — All rights reserved.