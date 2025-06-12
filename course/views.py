from django.shortcuts import render
from django.views import View
from urllib.parse import urlparse
import re


class OpenMiniAppLinkView(View):
    template_name = "index.html"

    def get(self, request):
        link = request.GET.get("link", "").strip()

        # Validate URL format
        if not link:
            return render(request, self.template_name, {"error": "No URL provided"})

        # Basic URL validation
        try:
            parsed = urlparse(link)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError("Invalid URL format")

            # Ensure proper URL format
            if not re.match(r'^https?://', link):
                link = f'https://{link}'

            # Security: Validate domains (optional but recommended)
            allowed_domains = [
                'youtube.com',
                'wordwall.net',
                'example.com'  # Add your allowed domains
            ]

            domain = parsed.netloc.lower()
            if not any(allowed in domain for allowed in allowed_domains):
                return render(request, self.template_name, {
                    "error": "This domain is not allowed in the Mini App"
                })

        except ValueError as e:
            return render(request, self.template_name, {
                "error": f"Invalid URL: {str(e)}"
            })
        except Exception as e:
            return render(request, self.template_name, {
                "error": f"Error processing URL: {str(e)}"
            })

        return render(request, self.template_name, {"link": link})