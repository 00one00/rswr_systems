from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add comprehensive security headers
    """
    
    def process_response(self, request, response):
        # Content Security Policy - Progressive security approach
        # Start with a permissive policy and gradually tighten
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://d3js.org https://cdn.jsdelivr.net https://cdn.tailwindcss.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://cdn.tailwindcss.com",
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.gstatic.com data:",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
            "object-src 'none'"
        ]
        
        # Only add CSP in production and if not already set
        if not response.get('Content-Security-Policy') and not getattr(request, '_skip_csp', False):
            response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Additional security headers (only if not already set by Django)
        if not response.get('X-Content-Type-Options'):
            response['X-Content-Type-Options'] = 'nosniff'
        if not response.get('X-Frame-Options'):
            response['X-Frame-Options'] = 'DENY'
        if not response.get('Referrer-Policy'):
            response['Referrer-Policy'] = 'same-origin'
        
        # Modern security headers
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=(), usb=()'
        
        # Add Cross-Origin Embedder Policy
        response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        
        # Add Cross-Origin Opener Policy
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        
        # Add Cross-Origin Resource Policy
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        return response