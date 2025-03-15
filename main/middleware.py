from django.shortcuts import redirect
from django.urls import reverse
from django.db import DatabaseError
from allauth.socialaccount.models import SocialAccount
import re

class SocialLoginErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except DatabaseError as e:
            error_msg = str(e)
            if "duplicate key error" in error_msg and "socialaccount_socialaccount" in error_msg:
                match = re.search(r'provider: "([^"]+)", uid: "([^"]+)"', error_msg)
                if match:
                    provider, uid = match.groups()
                    try:
                        social_account = SocialAccount.objects.get(provider=provider, uid=uid)
                        from django.contrib.auth import login
                        login(request, social_account.user)
                        return redirect(reverse('home'))
                    except Exception:
                        pass
            return redirect(reverse('login'))