# cms/middleware.py
from .models import ActivityLog

class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Skip logging for static files and admin
        if not request.path.startswith('/static/') and not request.path.startswith('/admin/'):
            if request.user.is_authenticated:
                ActivityLog.log_action(
                    request,
                    'PAGE_VIEW',
                    request.path,
                    f"{request.method} request"
                )
        
        return response
