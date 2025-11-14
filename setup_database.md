# Database Setup Guide

## Step 1: Install PostgreSQL
1. Download from https://www.postgresql.org/download/windows/
2. Run installer and follow the setup wizard
3. **Remember the password** you set for the `postgres` user
4. Keep default port: **5432**

## Step 2: Create the Database

### Option A: Using pgAdmin (GUI - Recommended for beginners)
1. Open **pgAdmin 4** (installed with PostgreSQL)
2. Connect to your PostgreSQL server (use the password you set during installation)
3. Right-click on "Databases" → "Create" → "Database"
4. Name: `product_importer`
5. Click "Save"

### Option B: Using Command Line (psql)
1. Open **Command Prompt** or **PowerShell**
2. Run:
   ```bash
   psql -U postgres
   ```
3. Enter your PostgreSQL password when prompted
4. Run:
   ```sql
   CREATE DATABASE product_importer;
   ```
5. Exit: `\q`

### Option C: Using SQL Shell (psql)
1. Open **SQL Shell (psql)** from Start Menu
2. Press Enter for all defaults (Server, Database, Port, Username)
3. Enter your password
4. Run:
   ```sql
   CREATE DATABASE product_importer;
   ```
5. Exit: `\q`

## Step 3: Create .env File
1. Copy `env.example` to `.env`:
   ```bash
   copy env.example .env
   ```
2. Edit `.env` and update with your credentials:
   ```
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/product_importer
   ```
   Replace `YOUR_PASSWORD` with the password you set during PostgreSQL installation.

## Step 4: Run Migrations
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Step 5: Verify Setup
Test the connection by running the app:
```bash
uvicorn app.main:app --reload
```

