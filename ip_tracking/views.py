from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ratelimit.decorators import ratelimit


def user_or_ip(request):
    """Use user.id if authenticated, otherwise fallback to IP address."""
    if request.user.is_authenticated:
        return str(request.user.id)
    return request.META.get("REMOTE_ADDR")


# Sensitive view with rate limiting
@csrf_exempt
@ratelimit(key="user_or_ip", rate="10/m", method="POST", block=True)
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def login_view(request):
    if request.method == "POST":
        return JsonResponse({"message": "Login attempt recorded."})
    return JsonResponse({"error": "Only POST allowed."}, status=405)
