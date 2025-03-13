FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
ENV ALLOWED_HOSTS=*
ENV RAILWAY_ENVIRONMENT=True

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["sh", "-c", "python manage.py migrate && gunicorn rs_systems.wsgi:application --bind 0.0.0.0:8000"] 