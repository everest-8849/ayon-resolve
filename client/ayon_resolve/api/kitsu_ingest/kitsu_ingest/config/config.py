import logging

class Settings:
    """
    Simple configuration class for Kitsu ingest.
    Values can be set programmatically or via environment variables.
    """
    def __init__(self):
        # Kitsu API configuration (will be overridden programmatically)
        self.kitsu_server: str = "http://localhost/api"
        self.kitsu_email: str = ""
        self.kitsu_password: str = ""
        
        # Default project settings
        self.default_fps: float = 25.0
        
        # Logging configuration
        self.log_level: str = "INFO"
        self.log_format: str = "[%(levelname)s][%(name)s] %(message)s"

settings = None

def get_settings():
    """Get or create the global settings instance."""
    global settings
    if settings is None:
        settings = Settings()
    return settings