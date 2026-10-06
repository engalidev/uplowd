# ============================================================
# routes/__init__.py
# Devspark ERP Update Server
# ============================================================

from .login import login_bp
from .admin import admin_bp

__all__ = [
    "login_bp",
    "admin_bp",
] 
