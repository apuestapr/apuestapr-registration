from typing import Dict, Any, Optional, List
from src.kyc_factory import KYCService
from src.models.registration import Registration

# Import existing Onfido functions
from src.onfido import (
    run_verification_request,
    generate_sdk_token,
    run_check,
    update_check_status
)

class OnfidoService(KYCService):
    """
    Onfido implementation of the KYC service.
    Wraps the existing Onfido functionality.
    """
    
    def init_verification(self, registration: Registration) -> Registration:
        """
        Initialize the Onfido verification process.
        This creates an applicant in Onfido's system.
        """
        return run_verification_request(registration)
    
    def generate_client_token(self, registration: Registration) -> str:
        """
        Generate the SDK token for the Onfido client-side library.
        """
        return generate_sdk_token(registration.onfido_applicant_id)
    
    def process_documents(self, registration: Registration, document_ids: List[str]) -> Registration:
        """
        Process uploaded document IDs and start the Onfido check.
        """
        registration.onfido_document_ids = document_ids
        return run_check(registration)
    
    def update_status(self, registration: Registration) -> Registration:
        """
        Check for updates to the verification status with Onfido.
        """
        return update_check_status(registration)
    
    def process_callback(self, data: Dict[str, Any], reference: Optional[str] = None) -> Optional[Registration]:
        """
        Process callback data from Onfido.
        In the current implementation, this functionality is handled differently,
        but we include it here for compatibility with our interface.
        """
        # Onfido currently uses polling rather than webhooks in this system
        # This is a placeholder for possible future webhook implementation
        return None 