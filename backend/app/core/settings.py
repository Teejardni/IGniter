from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import field_validator
import json
from pathlib import Path

class Settings(BaseSettings):
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]
    
    USER_AGENT_TWITTERBOT: str = "Twitterbot/1.0"
    USER_AGENT_GOOGLEBOT: str = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    USER_AGENT_FACEBOOKBOT: str = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
    USER_AGENT_GENERIC: str = "Mozilla/5.0 (PlayStation; PlayStation 5/6.50) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15"
    USER_AGENT_CHROME: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    HTTP_TIMEOUT_SECONDS: float = 12.0
    MAX_BYTES: int = 3_145_728  # ~3 MB
    BLOCKED_SITES_FILE: str = "app/blocked_sites.txt"
    GOOGLEBOT_SITES_FILE: str = "app/googlebot_sites.txt"  # Sites that work better with Googlebot
    ENABLE_OTEL: bool = False

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        if not value:
            return []
        
        if isinstance(value, str):
            # Handle JSON array
            if value.strip().startswith("["):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON array: {value}")
            
            # Handle comma-separated or single value
            return [x.strip() for x in value.split(",") if x.strip()]
        
        return value

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        env_nested_delimiter='__'
    )

    def _load_sites_from_file(self, filename: str) -> List[str]:
        """Helper method to load sites from a file."""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return [line.strip() for line in file if line.strip() and not line.strip().startswith('#')]
        except FileNotFoundError:
            print(f"Warning: {filename} not found.")
            return []
        except IOError as e:
            print(f"Error reading {filename}: {e}")
            return []

    @property
    def BLOCKED_SITES(self) -> List[str]:
        return self._load_sites_from_file(self.BLOCKED_SITES_FILE)

    @property
    def GOOGLEBOT_SITES(self) -> List[str]:
        return self._load_sites_from_file(self.GOOGLEBOT_SITES_FILE)

settings = Settings()