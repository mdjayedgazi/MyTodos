# 📝 MyTodos API — FastAPI Todo Application

> A modern, secure **Todo API** built with **FastAPI**, **SQLAlchemy 2.0** and **PostgreSQL** — featuring JWT authentication, role-based admin access, database migrations and a full pytest test suite. 🚀

---

## ✨ Features

- 🔐 **JWT Authentication** — login & token-protected endpoints
- 👑 **Role-Based Access** — admin-only routes (view/delete any todo)
- 📋 **Full CRUD** — create, read, update & delete todos
- 👤 **User Management** — registration, profile edit & password change
- 🧂 **Bcrypt Password Hashing** — never store plain text
- 🔒 **Schema-Safe Responses** — hashed passwords never leak
- 🗄️ **Alembic Migrations** — versioned database schema
- 🧪 **Pytest Coverage** — 10 tests covering auth, CRUD & admin permissions
- 📦 **`uv` Managed** — fast, reproducible dependency handling

---

## 🧰 Tech Stack

| Layer       | Technology                                    |
|-------------|-----------------------------------------------|
| ⚡ Framework | [FastAPI](https://fastapi.tiangolo.com/)      |
| 🗄️ ORM       | SQLAlchemy 2.0                                |
| 🐘 Database  | PostgreSQL (via psycopg)                      |
| 🔑 Auth      | python-jose (JWT) + passlib (bcrypt)          |
| 🧬 Migrations| Alembic                                      |
| ✅ Testing   | pytest + FastAPI TestClient                   |
| 📦 Tooling   | uv (Python 3.13)                             |

---

## 🗂️ Project Structure

```
.
├── app/                  # Core application
│   ├── main.py           # FastAPI app + todo/user endpoints
│   ├── models.py         # SQLAlchemy models (User, Todo)
│   ├── schema.py         # Pydantic schemas (request/response)
│   ├── config.py         # Settings from .env
│   ├── database.py       # Engine & session setup
│   └── dependencies.py   # get_db dependency
├── router/
│   ├── auth.py           # /auth/* endpoints + JWT helpers
│   └── admin.py          # /admin/* endpoints
├── alembic/              # Database migrations
├── tests/                # pytest test suite
├── .env                  # Environment variables (secrets)
├── compose.yml           # PostgreSQL + Adminer (docker)
└── pyproject.toml        # Project config & dependencies
```

---

## 🚀 Getting Started

### 1️⃣ Prerequisites

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL (local, Docker 🐳, or Neon cloud)

### 2️⃣ Installation

```bash
# Clone the repository
git clone https://github.com/mdjayedgazi/MyTodos.git
cd MyTodos

# Install dependencies
uv sync
```

### 3️⃣ Configure Environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/mytodo_db
SECRET_KEY=your-super-secret-random-key
ALGORITHM=HS256
```

### 4️⃣ Start PostgreSQL (optional, Docker)

```bash
docker compose up -d
```

### 5️⃣ Run Database Migrations

```bash
uv run alembic upgrade head
```

### 6️⃣ Start the Server 🎉

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open **Swagger UI** at 👉 <http://localhost:8000/docs> or **ReDoc** at <http://localhost:8000/redoc>

---

## 🔌 API Endpoints

### 📋 Todos — `app/main.py`

| Method | Endpoint               | Description            | Auth |
|--------|------------------------|------------------------|------|
| 🟢 GET | `/`                    | List my todos          | 🔐   |
| 🟢 GET | `/todo/{todo_id}`      | Get a specific todo    | 🔐   |
| 🟡 POST| `/create`              | Create a new todo      | 🔐   |
| 🟠 PUT | `/edit/{todos_id}`     | Update a todo          | 🔐   |
| 🔴 DEL | `/delete/{todo_id}`    | Delete a todo          | 🔐   |
| 🟢 GET | `/user`                | My profile (no secrets)| 🔐   |

### 👤 Authentication — `router/auth.py`

| Method | Endpoint               | Description                   |
|--------|------------------------|-------------------------------|
| 🟡 POST| `/auth/create-user`    | Register a new user 🧑‍💻       |
| 🟢 POST| `/auth/login`          | Login → get JWT token 🔑       |
| 🟠 PUT | `/auth/edituser`       | Update profile (first_name…)   |
| 🟠 PUT | `/auth/editpassword`   | Change password                |

### 👑 Admin — `router/admin.py` (role = `admin`)

| Method | Endpoint                   | Description                |
|--------|----------------------------|----------------------------|
| 🟢 GET | `/admin/todo`              | View **all** todos         |
| 🔴 DEL | `/admin/delete/{todo_id}`  | Delete any todo            |

### 🔑 Authentication Flow

```bash
# 1. Login
curl -X POST http://localhost:8000/auth/login \
  -F "username=tester" -F "password=secret123"

# 2. Use the token
curl http://localhost:8000/ \
  -H "Authorization: Bearer <access_token>"
```

---

## ✅ Running Tests

```bash
uv run pytest          # run all tests
uv run pytest -v       # verbose output
uv run pytest tests/test_todos.py -k admin   # filter by keyword
```

> 📦 Config lives in `pyproject.toml` (`testpaths = ["tests"]`, skips `.venv`/`data`).

---

## 🔒 Security Notes

- 🔑 `SECRET_KEY` lives in `.env` — **never commit it**
- 🧂 Passwords hashed with **bcrypt** before storage
- 🛡️ `UserResponse` schema guarantees `hashed_password` is never returned
- 👮 Admin endpoints verify `role == 'admin'` (403 for others)

---

## 🛠️ Useful Commands

```bash
uv run alembic revision --autogenerate -m "description"   # new migration
uv run alembic upgrade head                               # apply migrations
uv run alembic downgrade -1                               # roll back
uv run uvicorn app.main:app --reload                      # dev server
```

---

## 📄 License

This project is for **educational purposes** (FastAPI learning journey 🎓). Feel free to explore, break things, and rebuild them better!

---

<p align="center">
  Made with ❤️ & ☕ | <b>MyTodos API</b> ⚡ FastAPI
</p>
