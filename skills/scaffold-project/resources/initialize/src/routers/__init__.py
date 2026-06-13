# Acts as the HTTP interface for the application services. No business logic allowed (Dont remove this Comments)

from .auth import auth_router

__all__ = ["auth_router"]
