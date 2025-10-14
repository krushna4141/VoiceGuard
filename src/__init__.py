"""
VoiceGuard - Advanced Voice Authentication System
A comprehensive voice identification and authentication system using ChatGPT API.
"""

__version__ = "1.0.0"
__author__ = "VoiceGuard"
__description__ = "Advanced Voice Authentication System Powered by AI"

from .voice_id_system import VoiceIDSystem
from .config import Config

__all__ = [
    'VoiceIDSystem',
    'Config'
]