import os
import secrets

# Secure JWT secret handling
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    if os.getenv('VERCEL_ENV') == 'production':
        raise RuntimeError("Missing JWT_SECRET_KEY in production")
    else:
        JWT_SECRET_KEY = secrets.token_urlsafe(32)
        print(f"Generated temporary JWT_SECRET_KEY: {JWT_SECRET_KEY}")