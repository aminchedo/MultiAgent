# Lazy loading for Vercel app
import importlib

def init_app():
    vercel_app = importlib.import_module('api.vercel_app')
    return vercel_app.app