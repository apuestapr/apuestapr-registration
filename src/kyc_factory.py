from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from src.config import FeatureFlags
from src.models.registration import Registration

class KYCService(ABC):
    """
    Abstract base class for KYC services.
    Both Onfido and Shufti Pro services will implement this interface.
    """
    
    @abstractmethod
    def init_verification(self, registration: Registration) -> Registration:
        """
        Initialize the KYC verification process for a registration.
        Returns the updated registration object.
        """
        pass
    
    @abstractmethod
    def generate_client_token(self, registration: Registration) -> str:
        """
        Generate a token or URL needed for the client-side KYC process.
        """
        pass
    
    @abstractmethod
    def process_documents(self, registration: Registration, document_ids: List[str]) -> Registration:
        """
        Process document IDs (if applicable) and initiate the check process.
        """
        pass
    
    @abstractmethod
    def update_status(self, registration: Registration) -> Registration:
        """
        Check for updates to the KYC verification status.
        Returns the updated registration object.
        """
        pass
    
    @abstractmethod
    def process_callback(self, data: Dict[str, Any], reference: Optional[str] = None) -> Optional[Registration]:
        """
        Process callback data from the KYC provider.
        Returns the updated registration object if found.
        """
        pass


class KYCFactory:
    """
    Factory class for creating KYC service instances.
    """
    @staticmethod
    def get_service() -> KYCService:
        """
        Get the appropriate KYC service implementation based on configuration.
        """
        if FeatureFlags.is_shufti_enabled():
            # Lazy import to avoid circular dependencies
            from src.kyc_services.shufti_service import ShuftiService
            return ShuftiService()
        else:
            # Default to Onfido
            from src.kyc_services.onfido_service import OnfidoService
            return OnfidoService() 