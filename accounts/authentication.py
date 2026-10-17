from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions


class JWTQueryParamAuthentication(JWTAuthentication):
    """
    Authenticate against a JWT passed in the 'token' query parameter.
    Useful for browser-opened direct links (e.g., printable invoice pages)
    where setting Authorization headers is not possible.
    """

    def authenticate(self, request):
        raw_token = request.query_params.get('token')
        if not raw_token:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except exceptions.AuthenticationFailed:
            raise
        except Exception as e:
            raise exceptions.AuthenticationFailed(str(e))
