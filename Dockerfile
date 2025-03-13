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

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
ENV ALLOWED_HOSTS=*
ENV RAILWAY_ENVIRONMENT=True
ENV DJANGO_SETTINGS_MODULE=rs_systems.settings
ENV PYTHONPATH=/app

# Make verification script executable
RUN chmod +x verify_settings.py

# Expose port
EXPOSE 8000

# Run verification script, migrations, collect static files, and start the server
CMD ["sh", "-c", "python verify_settings.py && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn rs_systems.wsgi:application --bind 0.0.0.0:$PORT"] 