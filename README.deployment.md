# Django Spotify Backend Deployment Guide

This guide explains how to deploy this application using Docker and Docker Compose.

## Prerequisites

- Docker and Docker Compose installed on your server
- Domain name (optional, for production)
- SSL certificates (optional, for HTTPS)

## Deployment Steps

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd spotify.django.backend
```

### 2. Create environment file

Create a `.env` file in the project root with the following variables:

```
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here
DJANGO_ENV=production
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database Settings
DB_NAME=sptf
DB_USER=postgres_sptf
DB_PASSWORD=strong-database-password
DB_HOST=db
DB_PORT=5432
```

### 3. Configure Nginx (if using custom domain)

If you have a custom domain and SSL certificates:

1. Place your SSL certificates in `nginx/ssl/` directory:
   - `fullchain.pem`
   - `privkey.pem`

2. Update the server_name in `nginx/conf.d/default.conf` to your domain and uncomment the SSL section.

### 4. Deploy the application

```bash
# Start the production stack
docker-compose -f docker-compose.prod.yml up -d

# To see the logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 5. Create superuser (first time setup)

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Maintenance

### Database Backup

```bash
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres_sptf sptf > backup.sql
```

### Database Restore

```bash
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_sptf -d sptf
```

### Update Application

```bash
git pull
docker-compose -f docker-compose.prod.yml build web
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

- Check the logs: `docker-compose -f docker-compose.prod.yml logs -f`
- Restart containers: `docker-compose -f docker-compose.prod.yml restart`
- Inspect the database: `docker-compose -f docker-compose.prod.yml exec db psql -U postgres_sptf -d sptf` 