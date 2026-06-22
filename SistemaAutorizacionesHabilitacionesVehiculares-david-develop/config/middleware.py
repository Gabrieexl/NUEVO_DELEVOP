from django.shortcuts import render


class Custom404Middleware:
    """Renderiza una pagina 404 amigable para solicitudes HTML."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        accepts_html = "text/html" in request.headers.get("Accept", "")
        is_static_request = request.path.startswith("/static/") or request.path.startswith("/media/")

        if response.status_code == 404 and accepts_html and not is_static_request:
            return render(request, "404.html", status=404)

        return response
