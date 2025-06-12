from django.shortcuts import render
from django.views import View

class OpenMiniAppLinkView(View):
    template_name = "index.html"  # ✅ Don't include "templates/" here

    def get(self, request):
        link = request.GET.get("link")
        if not link:
            return render(request, self.template_name, {"error": "Link is missing"})

        # Optional domain validation
        allowed_domains = ["wordwall.net", "localhost"]
        # if not any(domain in link for domain in allowed_domains):
        #     return render(request, self.template_name, {"error": "Invalid link"})

        return render(request, self.template_name, {"link": link})
