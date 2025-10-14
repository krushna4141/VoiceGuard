"""
Configuration module for Voice ID System.
Handles environment variables and application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for Voice ID System."""
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Audio Configuration
    SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', 16000))
    CHANNELS = int(os.getenv('CHANNELS', 1))
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1024))
    RECORD_SECONDS = int(os.getenv('RECORD_SECONDS', 5))
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/voice_profiles.db')
    
    # Voice Identification Thresholds
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.8))
    MIN_CONFIDENCE_SCORE = float(os.getenv('MIN_CONFIDENCE_SCORE', 0.7))
    
    # Audio format
    FORMAT = 'float32'  # Audio format for processing
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        if cls.SAMPLE_RATE <= 0:
            raise ValueError("SAMPLE_RATE must be positive")
            
        if cls.CHANNELS not in [1, 2]:
            raise ValueError("CHANNELS must be 1 (mono) or 2 (stereo)")
            
        return True

# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration warning: {e}")
    print("Please set up your .env file based on .env.example")