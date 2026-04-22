import os
import logging
from dotenv import load_dotenv

# Load .env first (contains credentials and config), then .flaskenv (Flask settings)
load_dotenv('.env')
load_dotenv('.flaskenv')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get APP_URL and log it for debugging
app_url = os.getenv('APP_URL', 'https://localhost:5502')
logger.info(f"APP_URL from environment: {app_url}")

# Feature flags
class FeatureFlags:
    """
    Feature flags for controlling application behavior.
    These can be overridden via environment variables.
    """
    # KYC Provider flag - can be 'onfido' or 'shufti'
    KYC_PROVIDER = os.getenv('KYC_PROVIDER', 'onfido')
    logger.info(f"KYC_PROVIDER from environment: {KYC_PROVIDER}")
    
    @classmethod
    def is_shufti_enabled(cls):
        """
        Check if Shufti Pro should be used for KYC.
        """
        return cls.KYC_PROVIDER.lower() == 'shufti'
    
    @classmethod
    def is_onfido_enabled(cls):
        """
        Check if Onfido should be used for KYC.
        """
        return cls.KYC_PROVIDER.lower() == 'onfido'

    @classmethod
    def is_didit_enabled(cls):
        """
        Check if Didit should be used for KYC.
        """
        return cls.KYC_PROVIDER.lower() == 'didit'

# API credentials and other configuration values
class Config:
    """
    Application configuration settings.
    These are typically loaded from environment variables.
    """
    # Application URL for callback configuration
    APP_URL = app_url
    
    # Onfido settings
    ONFIDO_API_KEY = os.getenv('ONFIDO_API_KEY', '')
    
    # Shufti Pro settings
    SHUFTI_CLIENT_ID = os.getenv('SHUFTI_CLIENT_ID', '')
    SHUFTI_CLIENT_SECRET = os.getenv('SHUFTI_CLIENT_SECRET', '')
    SHUFTI_API_URL = os.getenv('SHUFTI_API_URL', 'https://api.shuftipro.com/')

    # Didit.me settings
    DIDIT_API_KEY = os.getenv('DIDIT_API_KEY', '')
    DIDIT_WORKFLOW_ID = os.getenv('DIDIT_WORKFLOW_ID', '') 