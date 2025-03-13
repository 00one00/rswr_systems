# Set the python version as a build-time argument
# with Python 3.12 as the default
ARG PYTHON_VERSION=3.12-slim-bullseye
FROM python:${PYTHON_VERSION}

# Set Python-related environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

# Create a working directory
WORKDIR /code

# Install os dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libjpeg-dev \
    libcairo2 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv && \
    pip install --upgrade pip

# Copy and install requirements first (for better caching)
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn

# Copy the project code (changes less frequently than requirements)
COPY ./src .

# Collect static files
RUN python manage.py collectstatic --noinput

# Set the Django default project name
ARG PROJ_NAME="cfehome"

# Create a runtime bash script with improved error handling
RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./paracord_runner.sh && \
    printf "# Attempt to run migrations, but continue if they fail\n" >> ./paracord_runner.sh && \
    printf "python manage.py migrate --no-input || echo 'Migration failed, but continuing startup.'\n\n" >> ./paracord_runner.sh && \
    printf "# Collect static files\n" >> ./paracord_runner.sh && \
    printf "python manage.py collectstatic --no-input || echo 'Static files collection failed, but continuing startup.'\n\n" >> ./paracord_runner.sh && \
    printf "# Start the Gunicorn server\n" >> ./paracord_runner.sh && \
    printf "gunicorn ${PROJ_NAME}.wsgi:application --bind \"[::]:\$RUN_PORT\"\n" >> ./paracord_runner.sh && \
    chmod +x paracord_runner.sh

# Create and switch to a non-root user for security
RUN useradd -m appuser
USER appuser

# Run the Django project via the runtime script
CMD ["./paracord_runner.sh"]