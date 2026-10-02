import threading


_state = threading.local()


def get_current_user():
    return getattr(_state, "user", None)


class AuditUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        _state.user = user if user is not None and user.is_authenticated else None
        try:
            return self.get_response(request)
        finally:
            _state.user = None
