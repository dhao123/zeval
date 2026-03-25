"""
Authentication constants for SSO integration.
"""
from app.core.config import settings


class AuthConstants:
    """Authentication related constants."""
    
    # Security service hosts for different environments
    # Use direct security service URL for backend access
    __hosts = {
        "security": {
            "PRO": "http://security-service-zkh360-com.share:8080",
            "UAT": "https://security-service-uat.zkh360.com",
            "LOCAL": "https://security-service-uat.zkh360.com",
        }
    }
    
    # Admin role ID (from config or default)
    @property
    def admin_role_id(self) -> int:
        return getattr(settings, 'ADMIN_ROLE_ID', 1885)
    
    @staticmethod
    def get_security_host() -> str:
        """
        Get security service host based on current environment.
        
        Returns:
            str: The security service base URL
        """
        env = getattr(settings, 'ENVIRONMENT', 'development')
        # Map environment names
        if env == "production" or env == "PRO":
            return AuthConstants.__hosts["security"]["PRO"]
        elif env == "uat" or env == "UAT":
            return AuthConstants.__hosts["security"]["UAT"]
        else:  # development, local, etc.
            return AuthConstants.__hosts["security"]["LOCAL"]


# Global constants instance
auth_constants = AuthConstants()
