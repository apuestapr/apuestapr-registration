from typing import Dict, Any, Optional, List
from src.models.registration import Registration

class KYCService:
    """
    Base interface for KYC service implementations.
    All KYC service providers must implement this interface.
    """
    
    def init_verification(self, registration: Registration) -> Registration:
        """
        Initialize the verification process with the KYC provider.
        This typically creates an applicant/user in the provider's system.
        """
        raise NotImplementedError("KYC service must implement init_verification")
    
    def generate_client_token(self, registration: Registration) -> str:
        """
        Generate a token for client-side verification UI.
        This might be an SDK token, iframe URL, or other mechanism.
        """
        raise NotImplementedError("KYC service must implement generate_client_token")
    
    def process_documents(self, registration: Registration, document_ids: List[str]) -> Registration:
        """
        Process document IDs and start the verification check.
        """
        raise NotImplementedError("KYC service must implement process_documents")
    
    def update_status(self, registration: Registration) -> Registration:
        """
        Check for updates to the verification status.
        """
        raise NotImplementedError("KYC service must implement update_status")
    
    def process_callback(self, data: Dict[str, Any], reference: Optional[str] = None) -> Optional[Registration]:
        """
        Process callback data from the KYC provider.
        """
        raise NotImplementedError("KYC service must implement process_callback")