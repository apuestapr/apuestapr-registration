> Is immediate feedback crucial, or would instructing the user that they'll be notified/redirected upon completion (requiring manual refresh or navigation away) be sufficient initially? Adding polling/WebSockets increases complexity.

Shufti's iframe is created from a verification URL that is aware of the redirect path. The iframe should handle the redirect automatically, and the page which they are redirected to should be aware of the user's verification status in real time. They should already be aware of the verification verdict before they are redirected, because it is the user themself that is the one to press the Proceed button after the verification process is completed.

> Shufti Callback Details: The plan correctly highlights the need to consult Shufti's documentation. Do you have access to the specific callback payload structure and the full list of possible event types (e.g., verification.accepted, verification.declined, request.invalid, request.timeout, request.deleted, etc.)? Knowing these specifics is vital for accurate state mapping and handling.

request.pending
request.invalid
verification.cancelled
request.timeout
request.unauthorized
verification.accepted
verification.declined
verification.status.changed
request.deleted
request.received

You can also consult this website in the future for docs: `https://shuftipro.com/help-center/response-events/`

Don't do anything yet. I'm just hitting send to remember where I left off.
