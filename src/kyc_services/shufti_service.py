import uuid
import logging
import datetime
from typing import Dict, Any, Optional, List
from src.kyc_services.base import KYCService
from src.models.registration import Registration
from src.config import Config
from src.kyc_services.implementations import shufti_impl

logger = logging.getLogger(__name__)

class ShuftiService(KYCService):
    """
    Shufti Pro implementation of the KYC service.
    """
    
    def init_verification(self, registration: Registration) -> Registration:
        """
        Initialize the Shufti Pro verification process.
        Generates a reference ID and prepares the registration record.
        """
        # Generate a reference ID in the format [INITIALS]-[UUID]
        initials = self._get_initials(registration)
        reference = f"{initials}-{str(uuid.uuid4())}"
        
        # Store the reference ID and mark this as using Shufti Pro
        registration.shufti_reference = reference
        registration.kyc_provider = 'shufti'
        registration.save()
        
        return registration
    
    def generate_client_token(self, registration: Registration) -> str:
        """
        Make an API call to Shufti Pro to get the verification URL.
        This URL will be used in an iframe for the user to complete KYC.
        """
        # Check if we already have a valid verification URL for a pending request
        if registration.shufti_reference and registration.kyc_status == 'PENDING':
            if registration.shufti_callback_payload:
                payload = registration.shufti_callback_payload
                if isinstance(payload, dict) and 'verification_url' in payload:
                    logger.info(f"Returning existing verification URL for {registration.shufti_reference}")
                    return payload['verification_url']
            
            # If we have a reference but no URL, we must generate a new reference 
            # because Shufti will reject a duplicate POST with the same reference.
            logger.info(f"Generating new reference for pending request {registration.id} to avoid duplicate reference error")
            registration = self.init_verification(registration)
            
        # If the reference doesn't exist or if this is a retry of a failed verification,
        # generate a new reference
        elif not registration.shufti_reference or registration.kyc_status == 'FAILED':
            if registration.shufti_reference and registration.kyc_status == 'FAILED':
                logger.info(f"Regenerating reference for failed verification: {registration.id}")
            registration = self.init_verification(registration)
            
        # Build the payload for Shufti API
        payload = self._build_verification_payload(registration)
        
        # Make the API call to Shufti
        try:
            response = shufti_impl.call_shufti_api(payload)
            
            if 'error' in response:
                logger.error(f"Shufti API error: {response['error']}")
                return ""
                
            if 'verification_url' in response:
                # Store the response for debugging
                registration.shufti_callback_payload = response
                registration.save()
                
                return response['verification_url']
                
            logger.error(f"Unexpected response from Shufti API: {response}")
            return ""
            
        except Exception as e:
            logger.exception(f"Error calling Shufti API: {e}")
            return ""
    
    def process_documents(self, registration: Registration, document_ids: List[str]) -> Registration:
        """
        Process document IDs. Not applicable for Shufti's iframe flow,
        but included for interface compatibility.
        """
        # Shufti handles document processing within their iframe
        # This method won't be actively used but is defined for interface compatibility
        return registration
    
    def update_status(self, registration: Registration) -> Registration:
        """
        Check for updates to the verification status with Shufti.
        With Shufti Pro, we primarily rely on callbacks rather than polling.
        """
        # This is implemented mainly for interface compatibility
        # Shufti primarily uses callbacks to update status
        return registration
    
    def process_callback(self, data: Dict[str, Any], reference: Optional[str] = None) -> Optional[Registration]:
        """
        Process callback data from Shufti Pro.
        Updates the registration status based on Shufti's event type.
        """
        # Extract the reference from the callback data if not provided
        if not reference and data and 'reference' in data:
            reference = data.get('reference')
            
        if not reference:
            logger.error("No reference ID found in Shufti callback data")
            return None
            
        # Find the registration with this reference
        registration = Registration.find_one({'shufti_reference': reference})
        
        # If not found by reference, try by email if available
        if not registration and data.get('email'):
            logger.info(f"Trying to find registration by email: {data.get('email')}")
            email = data.get('email').lower()  # Normalize email to lowercase
            registration = Registration.find_one({'email': email})
            
            # If found by email, update the reference
            if registration:
                logger.info(f"Found registration by email {email}, updating reference to: {reference}")
                registration.shufti_reference = reference
                registration.save()
        
        if not registration:
            logger.error(f"No registration found with Shufti reference: {reference}")
            return None
            
        # Store the raw Shufti callback data for debugging/auditing
        registration.shufti_callback_payload = data
        
        # Add to callbacks array for history
        if not hasattr(registration, 'callbacks'):
            registration.callbacks = []
            
        # Store the callback data
        registration.callbacks.append({
            'timestamp': datetime.datetime.now(),
            'body': data
        })
        
        # Extract the event type
        event = data.get('event', '')
        
        # Map Shufti event types to our internal statuses
        if event == 'verification.accepted':
            registration.kyc_status = 'COMPLETE'
            registration.complete = True
        elif event == 'verification.declined':
            registration.kyc_status = 'FAILED'
        elif event == 'request.pending':
            registration.kyc_status = 'PENDING'
        elif event == 'request.received':
            registration.kyc_status = 'WAITING_FOR_CHECK_RESPONSE'
        elif event in ['request.invalid', 'verification.cancelled', 'request.timeout', 'request.unauthorised']:
            registration.kyc_status = 'FAILED'
        elif event == 'verification.status.changed':
            # For status changes, we should check the new status if possible
            # For now, we'll just log this event
            logger.info(f"Verification status changed for reference {reference}")
        elif event == 'request.deleted':
            registration.kyc_status = 'PENDING'
        else:
            logger.warning(f"Unknown Shufti event type: {event}")
            
        # Save the updated registration
        registration.save()
        
        return registration
    
    def _build_verification_payload(self, registration: Registration) -> Dict[str, Any]:
        """
        Build the payload for Shufti Pro API request.
        """
        # Use the configured APP_URL from environment variables
        app_url = Config.APP_URL
        
        # Get the callback and redirect URLs
        # Callback URL must use tunnel for Shufti server to reach it
        callback_url = f"{app_url}/kyc/shufti-callback"
        
        # For redirect URL, use both the tunnel URL and registration ID
        # The redirect handler will determine the appropriate final redirect based on the device
        redirect_url = f"{app_url}/registration/kyc/status/{registration.id}"
        
        # Log the URLs for debugging
        logger.info(f"Using callback URL: {callback_url}")
        logger.info(f"Using redirect URL: {redirect_url}")
        
        # Build the basic payload
        payload = {
            "reference": registration.shufti_reference,
            "callback_url": callback_url,
            "redirect_url": redirect_url,
            "email": registration.email,
            # "country": registration.country or "US",
            "language": "EN" if registration.preferred_language == 'en' else "ES",
            "verification_mode": "any",
            "ttl": 60,  # Time to live in minutes
        }
        
        # Add document verification
        payload["document"] = {
            # "name": {
            #     "first_name": registration.first_name,
            #     "last_name": registration.last_name
            # },
            # "dob": registration.birthday if registration.birthday else "",
            "supported_types": ["id_card", "driving_license", "passport"],
            "backside_proof_required": False,
        }
            
        return payload
    
    def _get_initials(self, registration: Registration) -> str:
        """
        Get the user's initials for the reference ID.
        """
        initials = ""
        
        if registration.first_name:
            initials += registration.first_name[0].lower()
            
        if registration.last_name:
            initials += registration.last_name[0].lower()
            
        if not initials:
            initials = "usr"
            
        return initials