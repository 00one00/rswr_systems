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

# Make railway_manage.py executable
RUN chmod +x railway_manage.py

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=True
ENV ALLOWED_HOSTS=*
ENV DJANGO_SETTINGS_MODULE=railway_settings
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run migrations, collect static files, and start the server
CMD ["sh", "-c", "python railway_manage.py migrate && python railway_manage.py collectstatic --noinput && gunicorn --log-level debug railway_wsgi:application --bind 0.0.0.0:$PORT"] 