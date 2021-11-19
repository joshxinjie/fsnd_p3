import json
from flask import request, abort, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev-7l04rrne.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffeeshop'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header
def get_token_auth_header():
    """
    Attempts to get the header from the request. Will raise 
    an AuthError if no header is present. Next, it will attempt 
    to split bearer and the token. Will raise an AuthError if 
    the header is malformed. Finally, it will return the token
    part of the header.

    Parameters
    ----------
    None
    
    Returns
    -------
    token:
      The JSON Web Token.
    """
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth.split()
    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    elif len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    elif len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    token = parts[1]
    return token

def check_permissions(permission, payload):
    """
    Raise an AuthError if permissions are not included in the payload.
    Raise an AuthError if the requested permission string is not in the 
    payload permissions array. Return true otherwise.

    !!NOTE check your RBAC settings in Auth0

    Parameters
    ----------
    permission: str
      Permission (i.e. 'post:drink')
    payload: 
      Decoded jwt payload
    
    Returns
    -------
    bool
      If permissions is in payload.
    """
    if 'permissions' not in payload:
                        raise AuthError({
                            'code': 'invalid_claims',
                            'description': 'Permissions not included in JWT.'
                        }, 400)

    if permission not in payload['permissions']:
        # abort(403)
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Unauthorized.'
        }, 403)
    return True

def verify_decode_jwt(token):
    """
    Verifies the JWT:
    - it should be an Auth0 token with key id (kid)
    - it should verify the token using Auth0 /.well-known/jwks.json
    - it should decode the payload from the token
    - it should validate the claims
    
    Return the decoded payload

    !!NOTE urlopen has a common certificate error described here: 
    https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org

    Parameters
    ----------
    token: str
      A json web token
      
    Returns
    -------
    payload:
      Decoded JWT payload
    """
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

def requires_auth(permission=''):
    """
    Function will
    - use the get_token_auth_header method to get the token
    - use the verify_decode_jwt method to decode the jwt
    - use the check_permissions method validate claims and check the requested permission
    - return the decorator which passes the decoded payload to the decorated method

    Parameters
    ----------
    permission: str
      String permission (i.e. 'post:drink')
      
    Returns
    -------
    requires_auth_decorator: decorator
    """
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except:
                # abort(401)
                raise AuthError({
                    'code': 'unauthorized',
                    'description': 'Permissions not found'
                }, 401)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator