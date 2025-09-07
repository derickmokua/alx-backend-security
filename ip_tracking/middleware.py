from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from ipgeolocation import ipgeolocation
from .models import RequestLog, BlockedIP


class IPLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = self.get_client_ip(request)

        # Block if IP is blacklisted
        if BlockedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("Access denied: Your IP is blocked.")

        # Geolocation (with caching)
        geo_data = cache.get(f"geo_{ip}")
        if not geo_data:
            try:
                geo = ipgeolocation.Api()
                geo_data = geo.get_geolocation(ip)
                cache.set(f"geo_{ip}", geo_data, timeout=60 * 60 * 24)  # 24h
            except Exception:
                geo_data = {}

        country = geo_data.get("country_name")
        city = geo_data.get("city")

        # Log request
        path = request.path
        RequestLog.objects.create(
            ip_address=ip,
            path=path,
            country=country,
            city=city
        )

    def get_client_ip(self, request):
        """Extract client IP address from request headers safely."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
