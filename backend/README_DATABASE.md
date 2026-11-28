
# BillWakeel Database Setup

BillWakeel uses SQLAlchemy ORM with SQLite for persistent bill storage.

## 1. Install dependencies

From the project root, run:

```bash
python -m pip install -r backend/requirements.txt
```

## 2. Database location

The SQLite database is created at:

```text
data/billwakeel.db
```

The `data/` directory is created automatically if it does not exist.

## 3. Initialize the database

Database tables are created automatically when the FastAPI application starts.

Run the backend from the `backend` directory:

```bash
cd backend
uvicorn main:app --reload
```

The application startup process calls `init_db()`, which creates all registered tables if they do not already exist.

## 4. Database models

The database currently contains:

- **Bill:** Stores uploaded bill information and extracted bill data.
- **Finding:** Stores individual findings associated with a bill, including charge details, explanation, source URL, and confidence.

A bill can have multiple findings. Deleting a bill also deletes its associated findings.

## 5. Database sessions

`SessionLocal` creates database sessions, and `get_db()` provides a session that is closed after use.

## 6. Important notes

- SQLite is used for local persistent storage.
- The database file is generated locally and should not be committed to Git.
- Tables are created automatically if they do not exist; existing records are preserved.
