"""
Health check middleware to bypass host validation for AWS ELB health checks.
This allows health checks to work without adding wildcards to ALLOWED_HOSTS.
"""
from django.http import JsonResponse
from django.db import connection


class HealthCheckMiddleware:
    """
    Middleware to handle health check requests from AWS ELB/ALB.
    Returns early for health check paths, bypassing ALLOWED_HOSTS validation.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle health check requests regardless of host header
        if request.path in ['/health/', '/health', '/healthcheck/', '/healthcheck']:
            return self.health_check_response(request)

        # Process normal requests
        response = self.get_response(request)
        return response

    def health_check_response(self, request):
        """
        Return health check response with database connectivity test.
        """
        try:
            # Test database connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

            return JsonResponse({
                'status': 'healthy',
                'service': 'rs_systems',
                'database': 'connected'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'unhealthy',
                'service': 'rs_systems',
                'error': str(e)
            }, status=500)