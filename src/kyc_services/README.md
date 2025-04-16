# KYC Services Architecture

This directory contains the service classes for integrating with KYC (Know Your Customer) providers.

## Architecture

The KYC services use a layered architecture:

```
src/
├── kyc_services/              # Service layer
│   ├── base.py                # KYCService interface
│   ├── onfido_service.py      # Onfido implementation of KYCService
│   ├── shufti_service.py      # Shufti Pro implementation of KYCService
│   └── implementations/       # Implementation details for each provider
│       ├── onfido_impl.py     # Onfido API functionality
│       └── shufti_impl.py     # Shufti Pro API functionality
└── kyc_factory.py             # Factory to create the appropriate service
```

## Usage

To use a KYC service, go through the factory:

```python
from src.kyc_factory import KYCFactory

# Get the configured KYC service
kyc_service = KYCFactory.get_service()

# Initialize verification
registration = kyc_service.init_verification(registration)

# Generate client token (for frontend SDK)
token = kyc_service.generate_client_token(registration)

# Process callbacks
registration = kyc_service.process_callback(callback_data)
```

## Adding a New Provider

To add a new KYC provider:

1. Create implementation details in `src/kyc_services/implementations/new_provider_impl.py`
2. Create a service class in `src/kyc_services/new_provider_service.py` that implements the `KYCService` interface
3. Update `src/kyc_services/__init__.py` to import and export the new service class
4. Add the new provider to the factory in `src/kyc_factory.py`

## Deprecation Notice

The old implementation files (`src/onfido.py` and `src/shufti.py`) are deprecated and maintained only for backward compatibility. All new code should use the service classes in `src/kyc_services` instead.
