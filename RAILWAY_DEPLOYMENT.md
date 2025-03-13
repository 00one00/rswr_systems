# Railway Deployment Guide

This document provides instructions for deploying this Django application on Railway.

## Prerequisites

- A Railway account
- A GitHub repository with this codebase

## Deployment Steps

1. **Fork or clone this repository to your GitHub account**

2. **Create a new project in Railway**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account if not already connected
   - Select the repository
   - Choose the `css-architecture-overhaul` branch

3. **Configure Environment Variables**
   - In your Railway project, go to the "Variables" tab
   - Add the following environment variables:
     - `SECRET_KEY`: A secure random string
     - `DEBUG`: Set to `False` for production
     - `ALLOWED_HOSTS`: Add your Railway domain (e.g., `.railway.app`)
     - `DATABASE_URL`: This will be automatically set by Railway if you add a PostgreSQL database
     - `STATIC_URL`: `/static/`
     - `STATIC_ROOT`: `/app/staticfiles/`
     - `TIME_ZONE`: Your preferred time zone (e.g., `America/Chicago`)

4. **Add a PostgreSQL Database**
   - In your Railway project, click "New"
   - Select "Database" and then "PostgreSQL"
   - Railway will automatically set up the database and add the `DATABASE_URL` variable

5. **Deploy the Application**
   - Railway will automatically deploy your application based on the `railway.json` configuration
   - You can monitor the deployment in the "Deployments" tab

6. **Access Your Application**
   - Once deployed, you can access your application using the domain provided by Railway
   - The domain can be found in the "Settings" tab under "Domains"

## Troubleshooting

- **Database Migrations**: If you need to run migrations manually, you can use the Railway CLI or the Railway dashboard to run the command: `python manage.py migrate`
- **Static Files**: If static files are not being served correctly, ensure that `STATIC_URL` and `STATIC_ROOT` are set correctly in your environment variables
- **Logs**: Check the logs in the Railway dashboard for any errors or issues

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/) 