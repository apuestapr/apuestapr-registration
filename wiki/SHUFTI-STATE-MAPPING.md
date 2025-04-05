# Shufti Pro Event to Internal KYC Status Mapping

This document defines how Shufti Pro event types map to our internal KYC status values, ensuring accurate state management during and after the verification process.

## Current Internal KYC Status Values

Our application currently uses the following internal status values for KYC verification:

- `PENDING`: Initial state when a user has started but not completed KYC verification
- `WAITING_FOR_CHECK_RESPONSE`: Verification data submitted, awaiting KYC provider response
- `COMPLETE`: Verification was successful
- `FAILED`: Verification was unsuccessful

## Shufti Pro Events

Based on Shufti Pro's documentation, the following event types may be received in callbacks:

- `request.pending`: Verification link generated but process not completed
- `request.invalid`: Parameters in request payload not in correct format
- `verification.cancelled`: User did not agree to terms & conditions
- `request.timeout`: Verification not completed within time limit
- `request.unauthorised`: Auth header incorrect
- `verification.accepted`: Verification successful
- `verification.declined`: Verification unsuccessful
- `verification.status.changed`: Verification status changed from back office
- `request.deleted`: Verification data deleted
- `request.received`: Verification request received (offsite verification only)

## Mapping From Shufti Events to Internal Status

| Shufti Event                  | Internal KYC Status          | Notes                                                         |
| ----------------------------- | ---------------------------- | ------------------------------------------------------------- |
| `request.pending`             | `PENDING`                    | User has initiated but not completed the verification process |
| `request.invalid`             | `FAILED`                     | Invalid parameters were provided                              |
| `verification.cancelled`      | `FAILED`                     | User cancelled the verification                               |
| `request.timeout`             | `FAILED`                     | Verification timed out                                        |
| `request.unauthorised`        | `FAILED`                     | Authentication issue with Shufti                              |
| `verification.accepted`       | `COMPLETE`                   | Verification completed successfully                           |
| `verification.declined`       | `FAILED`                     | Verification completed but was declined                       |
| `verification.status.changed` | _Special handling_           | Requires checking the new status in Shufti's system           |
| `request.deleted`             | `PENDING`                    | Data deleted, user should restart verification                |
| `request.received`            | `WAITING_FOR_CHECK_RESPONSE` | Offsite verification in progress                              |

## Implementation Considerations

1. **State Transitions**:

   - Not all transitions between states make sense (e.g., from `COMPLETE` back to `PENDING`).
   - The callback handler should validate state transitions and log unexpected ones.

2. **Additional State Information**:

   - Store the raw Shufti response in `shufti_callback_payload` for debugging.
   - Consider storing a more detailed status code (e.g., `FAILED_TIMEOUT`, `FAILED_CANCELLED`) internally if more specific user messaging is required.

3. **Handling `verification.status.changed`**:

   - When receiving this event, the callback should make an API call to Shufti to get the current status.
   - Alternatively, if Shufti includes the new status in this callback, use that to update the internal state.

4. **Recovery from Failed States**:
   - Define in the application logic how a user can retry verification after reaching a `FAILED` state.
   - Consider implementing a counter for verification attempts and a cooldown period.
