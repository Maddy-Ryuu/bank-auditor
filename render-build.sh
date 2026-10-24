#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "============================================="
echo " Bank Fee Auditor — Render Build Pipeline"
echo "============================================="

echo "[1/3] Installing Python backend dependencies..."
pip install -r backend/requirements.txt

echo "[2/3] Installing frontend dependencies and compiling React production bundle..."
cd frontend
npm install
npm run build
cd ..

echo "[3/3] Applying Alembic database migrations to PostgreSQL..."
alembic upgrade head

echo "Build and database schema migration completed successfully."
