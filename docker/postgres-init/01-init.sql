-- Ensure the database exists (safe to run multiple times)
SELECT 'CREATE DATABASE fitness_platform'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'fitness_platform')\gexec
