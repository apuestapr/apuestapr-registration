const express = require("express");
const axios = require("axios");
const bodyParser = require("body-parser");
const app = express();
const port = 3000;

// Middleware to parse JSON bodies
app.use(bodyParser.json());

// Endpoint to start the KYC process
app.post("/start-kyc", async (req, res) => {
  // Get the custom reference ID from the front-end request
  const { reference } = req.body;
  if (!reference) {
    return res.status(400).json({ error: "Reference ID is required" });
  }

  // Predefined parameters to send to Shufti Pro
  const payload = {
    reference: reference, // use the provided reference ID
    callback_url:
      "https://576b-2600-4041-5514-0-553d-4f70-9be4-50a3.ngrok-free.app/shufti-callback", // replace with your actual callback URL
    redirect_url:
      "https://576b-2600-4041-5514-0-553d-4f70-9be4-50a3.ngrok-free.app/thankyou", // replace with your actual redirect URL
    language: "EN",
    email: "user@example.com",
    country: "US",
    verification_mode: "any",
    document: {
      proof: "",
      supported_types: ["id_card", "driving_license", "passport"],
      name: {
        first_name: "",
        last_name: "",
      },
      additional_proof: "",
      dob: "",
      age: "",
      issue_date: "",
      expiry_date: "",
      document_number: "",
      allow_offline: "1",
      allow_online: "1",
      fetch_enhanced_data: "1",
      backside_proof_required: "0",
      verification_mode: "any",
      gender: "",
      show_ocr_form: "1",
      nationality: "",
    },
  };

  try {
    const response = await axios.post("https://api.shuftipro.com/", payload, {
      headers: {
        "Content-Type": "application/json",
        Authorization:
          "Basic N2QxNTM4MjhmM2MwNGNmMjA0MGQ2ZDczNjhjNWM2YmJiMWZjODBkMjhlNDdiYmQzMWI0YmYzOTZhY2UyODRkODp5aW1qMWNyNzJjN0ZsVE8xMkpQUmRyWDhuNHFKNDdBcg==",
      },
    });
    // Return the verification URL to the front end
    return res.json({
      verification_url: response.data.verification_url,
      message: "KYC process initiated successfully",
    });
  } catch (error) {
    console.error(
      "Error initiating KYC:",
      error.response ? error.response.data : error.message
    );
    return res.status(500).json({
      error: "Error initiating KYC process",
      details: error.response ? error.response.data : error.message,
    });
  }
});

// Endpoint to receive the callback from Shufti Pro
app.post("/shufti-callback", (req, res) => {
  console.log("Received callback from Shufti (headers):", req.headers);
  console.log("Received callback from Shufti (body):", req.body);
  // Here you can process the callback payload as needed
  res.json({ message: "Callback received" });
});

// Serve static files from the "public" folder (for the front end)
app.use(express.static("public"));

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
