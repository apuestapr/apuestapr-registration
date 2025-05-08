from typing import Dict, Any, Optional, List
from src.kyc_services.base import KYCService
from src.models.registration import Registration
from src.kyc_services.implementations import onfido_impl

class OnfidoService(KYCService):
    """
    Onfido implementation of the KYC service.
    """
    
    def init_verification(self, registration: Registration) -> Registration:
        """
        Initialize the Onfido verification process.
        This creates an applicant in Onfido's system.
        """
        # Mark the registration as using Onfido
        registration.kyc_provider = 'onfido'
        registration.started_at = registration.started_at or onfido_impl.datetime.datetime.now()
        registration.save()
        
        # Create the applicant in Onfido
        response = onfido_impl.create_applicant(registration)
        
        # Store the applicant ID
        registration.onfido_applicant_id = response['id']
        registration.save()
        
        return registration
    
    def generate_client_token(self, registration: Registration) -> str:
        """
        Generate the SDK token for the Onfido client-side library.
        """
        if not registration.onfido_applicant_id:
            raise ValueError("Onfido applicant ID not found")
            
        return onfido_impl.generate_sdk_token(registration.onfido_applicant_id)
    
    def process_documents(self, registration: Registration, document_ids: List[str]) -> Registration:
        """
        Process uploaded document IDs and start the Onfido check.
        """
        if not registration.onfido_applicant_id:
            raise ValueError("Onfido applicant ID not found")
            
        # Store the document IDs
        registration.onfido_document_ids = document_ids
        
        # Create the check
        check_response = onfido_impl.create_check(
            registration.onfido_applicant_id, 
            document_ids
        )
        
        # Store the check response
        registration.onfido_check_response = check_response
        registration.kyc_status = 'WAITING_FOR_CHECK_RESPONSE'
        registration.save()
        
        return registration
    
    def update_status(self, registration: Registration) -> Registration:
        """
        Check for updates to the verification status with Onfido.
        """
        if not registration.onfido_check_response:
            raise ValueError("No check data available")
            
        check_id = registration.onfido_check_response['id']
        check = onfido_impl.get_check_status(check_id)
        
        if check:
            registration.onfido_check_response = check
            
            done = False
            
            if check['status'] == 'complete':
                registration.kyc_status = 'COMPLETE'
                registration.complete = True
                done = True
                
            elif check['status'] == 'reopened':
                registration.kyc_status = 'FAILED'
                done = True
                
            if done:
                # Get the reports
                reports = onfido_impl.get_reports(check_id)
                registration.onfido_reports = reports
                
                # Update the user information from the reports
                for r in reports:
                    if r['name'] == 'document':
                        new_first_name = r['properties'].get('first_name')
                        if new_first_name:
                            registration.first_name = new_first_name
                        
                        new_last_name = r['properties'].get('last_name')
                        if new_last_name:
                            registration.last_name = new_last_name
                        
                        new_bday = r['properties'].get('date_of_birth')
                        if new_bday:
                            registration.birthday = new_bday
                
            registration.save()
        
        return registration
    
    def process_callback(self, data: Dict[str, Any], reference: Optional[str] = None) -> Optional[Registration]:
        """
        Process callback data from Onfido.
        In the current implementation, this functionality is handled by polling,
        but we include it for interface compatibility.
        """
        # Onfido currently uses polling rather than webhooks in this system
        # This is a placeholder for possible future webhook implementation
        return None