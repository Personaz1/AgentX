"""
NeuroRAT Agent Modules Package
------------------------------
This package contains extension modules for the NeuroRAT agent.
"""

__version__ = "1.0.0"
__author__ = "Mr. Thomas Anderson"

# Import modules for easier access
try:
    from . import keylogger
except ImportError:
    pass

__all__ = ['keylogger'] 