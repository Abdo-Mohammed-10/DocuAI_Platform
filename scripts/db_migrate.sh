#!/bin/bash
set -e

echo "Running database migrations..."
cd shared
alembic upgrade head
echo "Migrations complete."