# Database Setup for grupo-2-chave-ms-auth

This directory contains the database configuration for the authentication microservice.

## Docker Compose Setup

The database container is defined in the `docker-compose.yml` file located in the `chave-infra` directory.

### Service Configuration: chave-db

The `chave-db` service is configured as follows:

- **Build Context**: Uses the Dockerfile in this directory (`../grupo-2-chave-ms-auth/db`)
- **Container Name**: `chave-db`
- **Environment Variables** (sourced from `.env` file):
  - `POSTGRES_USER`: `${DB_USER}`
  - `POSTGRES_PASSWORD`: `${DB_PASSWORD}`
  - `POSTGRES_DB`: `${DB_NAME}`
- **Ports**: Maps `${DB_PORT}` on the host to port `5432` in the container
- **Volumes**: 
  - `postgres_data:/var/lib/postgresql/data` - Named volume for persistent database storage
- **Health Check**: Uses `pg_isready` to verify database readiness
- **Restart Policy**: `unless-stopped`

### Volume Setup

A named volume `postgres_data` is used to persist database data across container restarts and recreations. This volume is mounted to `/var/lib/postgresql/data` inside the container, ensuring that database files are not lost when the container is stopped or removed.

### Environment Variables

The container uses the following variables defined in the `.env` file:

- `DB_HOST`: Hostname for database connection (set to `chave-db` in compose)
- `DB_PORT`: Port for database connection (default: 5432)
- `DB_USER`: PostgreSQL username
- `DB_PASSWORD`: PostgreSQL password
- `DB_NAME`: Database name

### Initialization

The database is initialized using the `init.sql` script in this directory, which is executed when the container is first created.

## Running the Database

To start the database container:

1. Navigate to the `chave-infra` directory
2. Ensure the `.env` file has the required database variables set
3. Run: `docker-compose up chave-db`

The database will be available at `localhost:${DB_PORT}` with the credentials specified in the environment variables.