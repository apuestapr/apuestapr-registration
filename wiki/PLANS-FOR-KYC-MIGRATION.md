Okay, I understand the goal is to migrate the KYC process in your Flask application from Onfido to Shufti Pro, using the provided Node.js example as a reference, while carefully managing the impact on existing state management and application logic.

Let's break down how the blueprints and overall flow would likely need to change, aiming for simplification where possible.

**Comparison of Flows:**

- **Onfido (Current):**
  1.  Frontend requests user info validation (`/validate/...`).
  2.  Frontend requests KYC initiation (`/kyc/init/...`) -> Backend gets user details, calls Onfido API to create an applicant, gets an SDK token.
  3.  Backend renders processing page (`/kyc/process/...`) passing the SDK token.
  4.  Frontend initializes Onfido SDK with the token. User interacts with Onfido UI (via SDK).
  5.  Onfido SDK completion callback triggers frontend to POST document IDs (`/run-check/...`).
  6.  Backend receives document IDs, tells Onfido API to start the check, sets status to `WAITING_FOR_CHECK_RESPONSE`.
  7.  System relies on either polling (`/kyc/process/...` reloads and calls `update_check_status`) or a webhook (`/kyc/callback`) to get the final Onfido result (`COMPLETE`/`FAILED`).
- **Shufti Pro (Example & Proposed):**
  1.  Frontend requests user info validation (`/validate/...`) (This likely stays the same).
  2.  Frontend requests KYC initiation (`/registration/kyc/start/...`) -> Backend gets user details, generates a unique `reference` ID (e.g., `[INITIALS]-[UUID]`), calls Shufti API with payload (reference, callback URL, redirect URL, etc.). Shufti returns a `verification_url`.
  3.  Backend returns the `verification_url` to the frontend.
  4.  Backend renders a processing page (`/registration/kyc/status/...`) that embeds the `verification_url` in an iframe.
  5.  Frontend loads the `verification_url` into an iframe on the processing page. User interacts with Shufti UI within the iframe.
  6.  Shufti performs verification and sends the result asynchronously to the backend callback URL (`/kyc/shufti-callback`).
  7.  Backend callback handler receives the result, finds the `Registration` via the `shufti_reference` ID, updates `kyc_status` (`COMPLETE`/`FAILED`/etc. based on Shufti's event), and saves relevant data.
  8.  When verification completes within the iframe, Shufti redirects the iframe to the specified `redirect_url`, which should be a page that can check the current `kyc_status` from the database and display appropriate content.

**Blueprint Adjustments and Simplification (`pre_registration_bp`):**

Based on the proposed Shufti flow, we can simplify the endpoints:

1.  **Keep:** `/validate/<string:registration_id>` (POST)

    - Purpose: Validate user-entered data _before_ initiating costly KYC. This logic seems independent of the KYC provider.
    - No significant changes needed here.

2.  **Replace `/kyc/init/...` with `/registration/kyc/start/<string:registration_id>` (POST or PUT):**

    - Purpose: Initiate the Shufti KYC process.
    - Action:
      - Find the `Registration` object.
      - Ensure pre-validation passed.
      - Generate the Shufti `reference` using format `[INITIALS]-[UUID]` (e.g., `bg-28a9d680-5d89-4b6d-9c4f-a7ae8b8c1e3d`). Store this reference in a new field on the `Registration` model (e.g., `shufti_reference`).
      - Construct the payload for the Shufti API (like in `server.js`, ensuring `callback_url` points to your Flask app's callback and `redirect_url` specifies where to send the user after verification).
      - Call the Shufti API using credentials stored securely (e.g., from `.flaskenv`).
      - Handle potential errors from the Shufti API call.
      - If successful, get the `verification_url` from Shufti's response.
      - Return JSON: `{ "success": true, "verification_url": "..." }` or `{ "success": false, "error": "..." }`.

3.  **Replace `/kyc/process/...` with `/registration/kyc/status/<string:registration_id>` (GET):**

    - Purpose: Display the KYC status and the Shufti iframe if applicable.
    - Action:
      - Find the `Registration` object.
      - Render a template (e.g., `registration-shufti-process.html`).
      - Pass the `registration` object (including current `kyc_status`) to the template.
      - The template will:
        - If `kyc_status` is `PENDING` (or a new "awaiting iframe" state), make a client-side fetch to `/registration/kyc/start/...` to get the `verification_url` and load it into an iframe.
        - If `kyc_status` is `WAITING_FOR_CHECK_RESPONSE` (or equivalent Shufti waiting state), show a "Processing..." message.
        - If `kyc_status` is `COMPLETE` or `FAILED`, show the final status message.

4.  **Adapt `/kyc/callback` to `/kyc/shufti-callback` (POST):**

    - Purpose: Receive asynchronous status updates from Shufti. This is CRITICAL.
    - Action:
      - Receive the POST request from Shufti. **Crucially, consult Shufti Pro documentation for the exact structure of their callback payload and event types.**
      - Extract the `reference` ID from the payload.
      - Find the `Registration` object using `Registration.find_one({'shufti_reference': reference})`.
      - Extract the verification status/event type from the Shufti payload (e.g., `verification.accepted`, `verification.declined`, `request.invalid`, `request.timeout`, etc.).
      - **Map Shufti statuses to your internal `kyc_status`:** (See `wiki/SHUFTI-STATE-MAPPING.md` for detailed mapping)
      - Store relevant data from the Shufti callback payload onto the `Registration` model (e.g., replacing `onfido_check_response` with `shufti_callback_payload`, or extracting specific verified data points if needed).
      - Save the updated `Registration` object.
      - Return an appropriate response to Shufti (usually a 200 OK).

5.  **Remove `/run-check/...`:**
    - This endpoint seems specific to Onfido's flow (submitting document IDs after capture). The Shufti iframe flow likely handles document submission and checking initiation together, making this separate step unnecessary.

**Summary of Simplification:**

- Reduced the number of primary KYC-related endpoints from ~4 (init, process, run-check, callback) to ~3 (start, status, callback).
- Shifted complexity from frontend SDK integration (Onfido) to backend callback handling (Shufti).
- The frontend interaction becomes simpler: get a URL, load an iframe.

**Key Considerations:**

- **State Mapping:** Carefully define how Shufti's event statuses map to your existing `PENDING`, `WAITING_FOR_CHECK_RESPONSE`, `COMPLETE`, `FAILED` states. See the separate document `wiki/SHUFTI-STATE-MAPPING.md` for detailed mapping between Shufti event types and internal state.

- **Model Changes:** Update `src/models/registration.py`. Remove Onfido fields (`onfido_applicant_id`, `onfido_check_response`, `onfido_document_ids`, `onfido_reports`). Add Shufti fields (`shufti_reference`, potentially `shufti_callback_payload`).

- **Configuration:** Add Shufti API credentials and endpoint URL to `.flaskenv`.

- **Error Handling:** Implement robust error handling for both the API calls _to_ Shufti (`/start`) and the callbacks _from_ Shufti (`/callback`). Some key scenarios to consider include:

  - Handling API failures when calling Shufti's API
  - Managing cases where callbacks contain unexpected payloads
  - Dealing with missing Registration records when callbacks arrive
  - These scenarios will be expanded in more detail in future planning.

- **Security Considerations:** While not a priority for the initial implementation, consider implementing signature verification for callbacks from Shufti to ensure the requests genuinely originate from Shufti. This would involve validating the signature included in request headers against a shared secret.

- **Transition Plan for Existing Users:** This migration targets the KYC _process_ for new registrations or users with pending verification. Users who have already completed verification via Onfido will retain their `COMPLETE` status, and those previously marked as `FAILED` will remain so unless they re-initiate the KYC process.

**Feature Flagging Strategy:**

To ensure a smooth transition from Onfido to Shufti Pro, a feature flag approach will be implemented:

1. **Flag Implementation:**

   - Add a configuration variable (e.g., `KYC_PROVIDER`) in `.flaskenv` that can be set to either `"onfido"` or `"shufti"`.
   - Alternatively, implement a more sophisticated feature flag system that allows percentage-based rollout.

2. **Code Organization:**

   - Create separate service modules for each provider (e.g., `onfido_service.py` and `shufti_service.py`).
   - Implement a factory pattern to instantiate the appropriate service based on the feature flag.
   - Keep both route handlers active but use the feature flag to determine which one processes the request.

3. **Route Handling:**

   - For a cleaner transition, maintain both sets of routes (`/kyc/init`, `/kyc/process`, etc. for Onfido and `/registration/kyc/start`, `/registration/kyc/status`, etc. for Shufti).
   - In each route handler, check the feature flag to:
     - Process normally if it's the active provider
     - Redirect to the equivalent route of the active provider if it's not

4. **Database Considerations:**

   - Rather than removing Onfido fields from the `Registration` model immediately, keep them during the transition period.
   - Add the new Shufti fields to the model.
   - Consider adding a `kyc_provider` field to the model to explicitly track which provider was used for each registration.

5. **Rollout Strategy:**

   - Initially deploy with the flag set to `"onfido"` (or 0% Shufti) in production.
   - Test thoroughly in staging/test environments with the flag set to `"shufti"`.
   - Gradually increase the percentage of users directed to Shufti in production.
   - Monitor error rates, completion rates, and user feedback.
   - Once confident, set the flag to 100% Shufti.
   - After a suitable observation period with no issues, remove the Onfido code path.

6. **Rollback Plan:**
   - If issues arise with Shufti integration, flip the feature flag back to Onfido.
   - Ensure all routes continue to work with previously stored data from either provider.

This feature flag approach will allow both systems to coexist during the transition period, reducing risk and providing an easy rollback mechanism if needed.

This approach aims to integrate Shufti while simplifying the blueprint structure and leveraging the existing state management framework, provided the mapping between Shufti events and your internal states is handled carefully.
