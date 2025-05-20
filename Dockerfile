# Base Python image
FROM python:3.12.3-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Disable Chrome sandbox
ENV DISABLE_DEV_SHM_USAGE=1
ENV NO_SANDBOX=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    build-essential \
    libdbus-1-dev \
    pkg-config \
    libglib2.0-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Set up entrypoint
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Run the application
CMD ["./entrypoint.sh"]

# Expose port
EXPOSE 8000