# Shufti Pro KYC Integration Demo

This is a simple demo project showing how to integrate Shufti Pro's KYC service.

## Setup

1. Install dependencies:

```
npm install
```

2. Run the server:

```
npm start
```

3. Open your browser and navigate to `http://localhost:3000`

## How It Works

1. Click the "Start KYC Process" button on the webpage
2. The frontend sends a request to your backend with a reference ID
3. Your backend uses this reference ID to call Shufti Pro's API
4. The backend returns the verification URL to the frontend
5. The frontend loads this URL in an iframe for the user to complete the KYC process
6. Once completed, Shufti Pro will send a callback to your `/shufti-callback` endpoint

## Important Notes

- The authentication credentials are directly embedded in the code for demo purposes only
- In a production environment, store credentials securely (e.g., environment variables)
- Replace callback and redirect URLs with your actual URLs
