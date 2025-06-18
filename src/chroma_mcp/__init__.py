# Export server and client functionality

from .server import main
from .client import ChromaMCP

# Make http_server module available
try:
    from . import http_server
except ImportError:
    pass

__all__ = ["main", "ChromaMCP", "http_server"]
