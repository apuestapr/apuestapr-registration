# KYC Flow States

This document outlines the states of the Know Your Customer (KYC) process as saved in the `kyc_status` field of the `Registration` model in MongoDB during user pre-registration.

The states are primarily managed within `src/onfido.py` and referenced in `src/blueprints/pre_registration.py`. The `Registration` model itself is defined in `src/models/registration.py`.

## States

1.  **`PENDING`**:

    - The initial default state when a `Registration` record is created.
    - Indicates that the KYC process has not yet been seriously initiated for the user.
    - Set in `src/models/registration.py`.

2.  **`WAITING_FOR_CHECK_RESPONSE`**:

    - Set after the required user documents have been submitted to Onfido and a background check has been initiated.
    - The system is waiting for Onfido to return the results of the check.
    - Set in the `run_check` function in `src/onfido.py`.

3.  **`COMPLETE`**:

    - Set when the Onfido check returns successfully, indicating the user has passed KYC verification.
    - Set in the `update_check_status` function in `src/onfido.py`.

4.  **`FAILED`**:
    - Set when the Onfido check returns with a status indicating failure or an issue requiring review (specifically, when Onfido status is 'reopened').
    - Set in the `update_check_status` function in `src/onfido.py`.
