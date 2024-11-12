#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

# Default values
DB_NAME=${DB_NAME:-"fabled"}
DB_USER=${DB_USER:-"postgres"}
DB_PASSWORD=${DB_PASSWORD:-"asd123"}

# Create database if it doesn't exist
echo "Checking if database exists..."
if ! PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "Creating database $DB_NAME..."
    PGPASSWORD=$DB_PASSWORD createdb -U $DB_USER $DB_NAME
else
    echo "Database $DB_NAME already exists"
fi

# Drop the alembic_version table if it exists
echo "Resetting migration state..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -c "DROP TABLE IF EXISTS alembic_version;"

# Remove existing migrations directory
echo "Removing existing migrations..."
rm -rf migrations/

# Reinitialize migrations
echo "Initializing fresh migrations..."
flask db init

# Create initial migration
echo "Creating initial migration..."
flask db migrate -m "Initial migration"

# Apply the migration
echo "Applying migration..."
flask db upgrade

echo "Migration reset complete!"