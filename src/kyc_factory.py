import os
import logging
from typing import Optional
from src.kyc_services.base import KYCService

logger = logging.getLogger(__name__)

class KYCFactory:
    """
    Factory class for creating KYC service instances.
    """
    
    @staticmethod
    def get_service() -> KYCService:
        """
        Get a KYC service instance based on the configured provider.
        
        Returns:
            An instance of a KYCService implementation
        """
        provider = os.getenv('KYC_PROVIDER', 'onfido').lower()
        logger.info(f"Using KYC provider: {provider}")
        
        if provider == 'onfido':
            from src.kyc_services import OnfidoService
            return OnfidoService()
        elif provider == 'shufti':
            from src.kyc_services import ShuftiService
            return ShuftiService()
        else:
            logger.warning(f"Unknown KYC provider: {provider}, defaulting to Onfido")
            from src.kyc_services import OnfidoService
            return OnfidoService()