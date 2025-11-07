# Docker Setup Guide

This project includes full Docker support for both backend and frontend services.

## Prerequisites

- Docker and Docker Compose installed
- `.env` files configured (see below)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Gabriel-Kelvin/multiagent.git
   cd multiagent
   ```

2. **Set up environment variables**
   
   Copy the example files and fill in your values:
   ```bash
   # Backend
   cp env.example .env
   # Edit .env with your actual values
   
   # Frontend
   cp frontend/env.example frontend/.env
   # Edit frontend/.env with your actual values
   ```

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:8011
   - Backend API: http://localhost:8010
   - Backend Health: http://localhost:8010/health

## Environment Variables

### Backend (.env)

Required variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `SUPABASE_POOLER_DSN` - Supabase connection string (pooler)
- `SUPABASE_DIRECT_DSN` - Supabase direct connection string

Optional variables:
- `SENDGRID_API_KEY` - For email functionality
- `EMAIL_FROM` - Sender email address
- `EMAIL_TO` - Recipient email address
- `DATA_TABLE` - Default table name for queries
- `FRONTEND_URL` - Frontend URL (for CORS)
- `BACKEND_URL` - Backend URL

See `env.example` for the complete list.

### Frontend (frontend/.env)

Required variables:
- `VITE_API_BASE_URL` - Backend API URL (e.g., `http://localhost:8010` or `http://13.212.129.11:8010`)
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key
- `VITE_APP_URL` - Frontend URL (for redirects)

See `frontend/env.example` for details.

## Deployment on AWS VM

1. **SSH into your VM**
   ```bash
   ssh user@13.212.129.11
   ```

2. **Clone the repository**
   ```bash
   git clone https://github.com/Gabriel-Kelvin/multiagent.git
   cd multiagent
   ```

3. **Set up environment variables**
   ```bash
   # Copy example files
   cp env.example .env
   cp frontend/env.example frontend/.env
   
   # Edit with your actual values
   nano .env
   nano frontend/.env
   ```

4. **Update frontend/.env for production**
   ```bash
   # Use the VM's IP or domain
   VITE_API_BASE_URL=http://13.212.129.11:8010
   VITE_APP_URL=http://13.212.129.11:8011
   ```

5. **Build and run**
   ```bash
   docker-compose up --build -d
   ```

6. **Check logs**
   ```bash
   docker-compose logs -f
   ```

7. **Stop services**
   ```bash
   docker-compose down
   ```

## Port Configuration

- **Backend**: Port 8010 (exposed on host)
- **Frontend**: Port 8011 (exposed on host)

To change ports, update `docker-compose.yml` and the corresponding environment variables.

## Health Checks

Both services include health checks:
- Backend: `GET /health`
- Frontend: `GET /health`

Check container health:
```bash
docker-compose ps
```

## Volumes

The following directories are mounted as volumes:
- `./artifacts` → `/app/artifacts` (backend)
- `./logs` → `/app/logs` (backend)

This ensures data persists between container restarts.

## Troubleshooting

### Frontend can't connect to backend

1. Check that `VITE_API_BASE_URL` in `frontend/.env` matches the backend URL
2. For Docker, use `http://localhost:8010` (browser-accessible URL)
3. Ensure CORS is configured in backend (already set to allow all origins)

### Build fails

1. Check that all required environment variables are set
2. Verify Docker and Docker Compose are up to date
3. Check logs: `docker-compose logs backend` or `docker-compose logs frontend`

### Port conflicts

If ports 8010 or 8011 are already in use:
1. Stop the conflicting service
2. Or change ports in `docker-compose.yml`

## Development vs Production

### Local Development (without Docker)
- Backend: `uvicorn server:app --reload --host 0.0.0.0 --port 8010`
- Frontend: `npm run dev` (runs on port 5173)

### Production (with Docker)
- Both services run in containers
- Frontend is built and served via nginx
- Backend runs with uvicorn

## Network

Both services are on the `multiagent-network` bridge network, allowing them to communicate using service names:
- Backend accessible at `http://backend:8010` (from within Docker network)
- Frontend accessible at `http://frontend:8011` (from within Docker network)

However, the browser needs external URLs (localhost or VM IP).

