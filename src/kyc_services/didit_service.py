import uuid
import logging
import datetime
from typing import Dict, Any, Optional, List
from src.kyc_services.base import KYCService
from src.models.registration import Registration
from src.config import Config
from src.kyc_services.implementations import didit_impl

logger = logging.getLogger(__name__)

class DiditService(KYCService):
    """
    Didit.me implementation of the KYC service.
    """
    
    def init_verification(self, registration: Registration) -> Registration:
        """
        Initialize the Didit.me verification process.
        """
        registration.kyc_provider = 'didit'
        registration.save()
        
        return registration
    
    def generate_client_token(self, registration: Registration) -> str:
        """
        Make an API call to Didit to get the verification URL.
        This URL will be used in an iframe or redirect for the user to complete KYC.
        """
        # If we already have a valid verification URL for a pending request, reuse it
        if registration.didit_session_id and registration.kyc_status == 'PENDING':
            if registration.didit_callback_payload:
                payload = registration.didit_callback_payload
                # Didit returns session_id and verification_url
                if isinstance(payload, dict) and 'url' in payload:
                    logger.info(f"Returning existing verification URL for Didit session {registration.didit_session_id}")
                    return payload['url']
        
        # We need to generate a new session
        # Ensure provider is set properly
        if registration.kyc_provider != 'didit':
            registration = self.init_verification(registration)
            
        payload = self._build_verification_payload(registration)
        
        try:
            response = didit_impl.call_didit_api(payload)
            
            if 'error' in response:
                logger.error(f"Didit API error: {response['error']}")
                return ""
                
            # Didit API typically returns something like {"session_id": "...", "url": "..."}
            # Adjust these keys based on Didit's actual response structure.
            # Here we assume it returns `session_id` and `url`.
            if 'url' in response:
                registration.didit_session_id = response.get('session_id', str(uuid.uuid4()))
                registration.didit_callback_payload = response
                registration.save()
                
                return response['url']
                
            logger.error(f"Unexpected response from Didit API: {response}")
            return ""
            
        except Exception as e:
            logger.exception(f"Error calling Didit API: {e}")
            return ""
            
    def process_documents(self, registration: Registration, document_ids: List[str]) -> Registration:
        """
        Process document IDs. Not applicable for Didit's hosted flow.
        """
        return registration

    def update_status(self, registration: Registration) -> Registration:
        """
        Check for updates to the verification status. We rely on webhooks.
        """
        return registration

    def process_callback(self, data: Dict[str, Any], reference: Optional[str] = None) -> Optional[Registration]:
        """
        Process callback data from Didit.me webhook.
        """
        # Didit webhook payload structure depends on their documentation.
        # Often they send a session_id or similar reference in the payload.
        # Assuming `session_id` is passed in the payload:
        session_id = data.get('session_id') or reference
        
        if not session_id:
            logger.error("No session_id found in Didit callback data")
            return None
            
        registration = Registration.find_one({'didit_session_id': session_id})
        
        if not registration:
            logger.error(f"No registration found with Didit session_id: {session_id}")
            return None
            
        # Add to callbacks array for history
        if not hasattr(registration, 'callbacks'):
            registration.callbacks = []
            
        registration.callbacks.append({
            'timestamp': datetime.datetime.now(),
            'body': data
        })
        
        # Adjust 'status' key and values based on Didit's actual webhook payload
        # Didit usually sends 'status' at top level or inside 'decision'
        status = data.get('status')
        if not status and 'decision' in data:
            status = data['decision'].get('status')
            
        status = str(status).lower() if status else ''
        
        # Didit also sends webhook_type like 'status.updated'
        webhook_type = data.get('webhook_type', '')
        
        if status in ('approved', 'accepted', 'completed'):
            registration.kyc_status = 'COMPLETE'
            registration.complete = True
        elif status in ('declined', 'rejected', 'failed', 'abandoned'):
            registration.kyc_status = 'FAILED'
        elif status in ('pending', 'in_progress', 'review', 'in review'):
            registration.kyc_status = 'WAITING_FOR_CHECK_RESPONSE'
        else:
            logger.warning(f"Unknown Didit status: {status} (Webhook type: {webhook_type})")
            
        registration.save()
        return registration

    def _build_verification_payload(self, registration: Registration) -> Dict[str, Any]:
        """
        Build the payload for Didit API request.
        """
        app_url = Config.APP_URL
        
        # Must include the /registration prefix because the blueprint is mounted there
        callback_url = f"{app_url}/registration/kyc/didit-callback"
        
        workflow_id = Config.DIDIT_WORKFLOW_ID
        if not workflow_id:
            logger.error("Didit workflow_id not configured")
            
        redirect_url = f"{app_url}/registration/kyc/status/{registration.id}"
        
        payload = {
            "workflow_id": workflow_id,
            "callback": callback_url,
            "redirect_url": redirect_url,
            "vendor_data": str(registration.id)  # Pass ID as metadata if supported
        }
        
        return payload
