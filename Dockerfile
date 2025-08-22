# Use Python 3.12 base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN apt-get update \
    && apt-get install build-essential tzdata -y \
    && python3 -m pip install --upgrade pip\
    && python3 -m pip install -r requirements.txt gunicorn uvicorn\
    && apt-get remove build-essential -y \
    && apt-get autoremove -y

# Copy the project code
COPY . .

# EXPOSE 8000
# CMD python manage.py migrate; python manage.py collectstatic --noinput; gunicorn find_your_trip_bd.asgi:application -w 1 -k uvicorn.workers.UvicornH11Worker -b 0.0.0.0:8000