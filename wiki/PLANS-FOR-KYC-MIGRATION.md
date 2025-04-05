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
  2.  Frontend requests KYC initiation (`/registration/kyc/start/...`) -> Backend gets user details, generates a unique `reference` ID (e.g., using the `registration_id`), calls Shufti API with payload (reference, callback URL, etc.). Shufti returns a `verification_url`.
  3.  Backend returns the `verification_url` to the frontend.
  4.  Backend renders a processing page (`/registration/kyc/status/...`).
  5.  Frontend loads the `verification_url` into an iframe on the processing page. User interacts with Shufti UI within the iframe.
  6.  Shufti performs verification and sends the result asynchronously to the backend callback URL (`/kyc/shufti-callback`).
  7.  Backend callback handler receives the result, finds the `Registration` via the `reference` ID, updates `kyc_status` (`COMPLETE`/`FAILED`/etc. based on Shufti's event), and saves relevant data.
  8.  The processing page (`/registration/kyc/status/...`) might need a mechanism (like periodic polling or WebSockets) to update its display once the callback is processed, or simply instruct the user they will be notified/redirected upon completion.

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
      - Generate the Shufti `reference` (e.g., use `registration_id`). Store this reference in a new field on the `Registration` model (e.g., `shufti_reference`).
      - Construct the payload for the Shufti API (like in `server.js`, ensuring `callback_url` points to your Flask app's callback).
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
        - If `kyc_status` is `WAITING_FOR_CHECK_RESPONSE` (or equivalent Shufti waiting state), show a "Processing..." message. _Consider adding a simple polling mechanism here to refresh the page or check status periodically if immediate feedback after callback is desired._
        - If `kyc_status` is `COMPLETE` or `FAILED`, show the final status message.

4.  **Adapt `/kyc/callback` to `/kyc/shufti-callback` (POST):**

    - Purpose: Receive asynchronous status updates from Shufti. This is CRITICAL.
    - Action:
      - Receive the POST request from Shufti. **Crucially, consult Shufti Pro documentation for the exact structure of their callback payload and event types.**
      - Extract the `reference` ID from the payload.
      - Find the `Registration` object using `Registration.find_one({'shufti_reference': reference})`.
      - Extract the verification status/event type from the Shufti payload (e.g., `verification.accepted`, `verification.declined`, `request.invalid`, `request.timeout`, etc.).
      - **Map Shufti statuses to your internal `kyc_status`:**
        - `verification.accepted` -> `COMPLETE`
        - `verification.declined` -> `FAILED`
        - Others (`request.invalid`, `request.timeout`, etc.) might map back to `PENDING` or `FAILED`, or you might introduce new internal statuses if you want to display more specific feedback.
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

- **State Mapping:** Carefully define how Shufti's event statuses map to your existing `PENDING`, `WAITING_FOR_CHECK_RESPONSE`, `COMPLETE`, `FAILED` states. Decide if you need more granular internal states. This mapping is vital for ensuring downstream logic (templating, account creation) continues to work correctly.
- **Model Changes:** Update `src/models/registration.py`. Remove Onfido fields (`onfido_applicant_id`, `onfido_check_response`, `onfido_document_ids`, `onfido_reports`). Add Shufti fields (`shufti_reference`, potentially `shufti_callback_payload`).
- **Configuration:** Add Shufti API credentials and endpoint URL to `.flaskenv`.
- **Error Handling:** Implement robust error handling for both the API calls _to_ Shufti (`/start`) and the callbacks _from_ Shufti (`/callback`).
- **Shufti Documentation:** All assumptions about Shufti's API and callback structure _must_ be verified against their official documentation.

This approach aims to integrate Shufti while simplifying the blueprint structure and leveraging the existing state management framework, provided the mapping between Shufti events and your internal states is handled carefully.
