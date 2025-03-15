from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if request.user.is_authenticated:
            try:
                social_account = SocialAccount.objects.get(
                    provider=sociallogin.account.provider,
                    uid=sociallogin.account.uid
                )
                if social_account.user != request.user:
                    return
            except SocialAccount.DoesNotExist:
                sociallogin.connect(request, request.user)