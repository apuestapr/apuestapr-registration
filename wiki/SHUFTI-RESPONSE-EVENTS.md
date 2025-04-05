# Response Events

Shufti provides the call-back URL functionality that can be accessed by specifying a parameter
within the API request. The call-back URL receives an update whenever there is a change in status.
The parameter for call-back URL is to be defined in the request payload as shown below:

```json

{
    "reference"    : "1234567",
    "callback_url" : "http://www.example.com/",
    "email"        : "johndoe@example.com",
    "country"      : "GB",
    "language"     : "EN",
    "redirect_url" : "http://www.example.com",
    "ttl"          : 60,
    "verification_mode" : "any",

    "document" :     {
    }
```

If the “callback_url” is specified in the verification payload, Shufti sends the
verification status to that URL.

The response events depend on the verification requestsent via API.

Kindly refer to the information below for details regarding response events and sample
call-back responses for each response event.

In this section
Response Events
Request Pending
Request Invalid
Verification Cancelled
Request Timeout
Request Unauthorised
Verification Declined
Verification Status Changed
Verification Accepted
Request Deleted
Request Recieved

request.pending
This event occurs only for onsite verification when the verification link has been generated but
the user has not gone through the entire process yet. This event is returned for all on-site verifications
until the verification is completed or timeout. The status returned to the callback URL is as follows;

```
         {
             "reference": "17374217",
             "event": "request.pending",
             "error": "",
             "verification_url": "https://app.shuftipro.com/process/verification/-------",
             "email": "johndoe@example.com",
             "country": "GB"
         }

request.invalid

The request invalid event occurs when the parameters specified in the request payload are not
of the correct format.

For example; the format of the date is incorrect, the address specified is less than 6 characters.

A sample response is attached for further elaboration;

```

    {
       "reference":"17374217",
       "event":"request.invalid",
       "error":{
          "service":"document",
          "key":"dob",
          "message":"The dob does not match the format Y-m-d."
       },
       "email":null,
       "country":null
    }


verification.cancelled
The “verification.cancelled” event occurs when the end-user does not agree to the terms and conditions
shown at the beginning of the verification flow. This event only occurs for on-site verifications.

A sample response is attached for further clarification;

```
    {
       "reference":"17374217",
       "event":"verification.cancelled",
       "error":""
    }

request.timeout
Shufti has a time-limit for verifications to be performed after the verification link is generated.
By default, the time limit is 60 minutes. This limit can be changed by using a specified
parameter as shown below;

```

    {
       "reference":"1234567",
       "callback_url":"http://www.example.com/",
       "email":"johndoe@example.com",
       "country":"GB",
       "language":"EN",
       "redirect_url":"http://www.example.com",
       "ttl":60,
       "verification_mode":"any",
       "document":{

    }


The sample response for when a request is timed-out is given below;

```
    {
       "reference":"17374217",
       "event":"request.timeout",
       "error":""
    }

request.unauthorised
The “request.unauthorised” event occurs when the auth header is not correct. To resolve this error
make sure the API keys are correct. API keys are accessible through the Shufti back-office.

```

    {
       "reference":"",
       "event":"request.unauthorized",
       "error":{
          "service":"",
          "key":"",
          "message":"Authorization keys are missing/invalid."
       },
       "email":null,
       "country":null
    }


verification.accepted
For accepted verifications, the event of “verification.accepted” occurs. This response is returned
in the HTTP response and the callback as well.

For accepted verification, a sample response is provided below;

```
    {
       "reference":"17374217",
       "event":"verification.accepted",
       "error":"",
       "verification_result":{
          "document":{
             "name":1,
             "dob":1,
             "expiry_date":1,
             "issue_date":1,
             "document_number":1,
             "document":1,
             "gender":""
          },
          "address":{
             "name":1,
             "full_address":1
          }
       },
       "verification_data":{
          "document":{
             "name":{
                "first_name":"John",
                "middle_name":"Carter",
                "last_name":"Doe"
             },
             "dob":"1978-03-13",
             "issue_date":"2015-10-10",
             "expiry_date":"2025-12-31",
             "document_number":"1456-0989-5567-0909",
             "selected_type":[
                "id_card"
             ],
             "supported_types":[
                "id_card",
                "driving_license",
                "passport"
             ],
             "gender":"M"
          },
          "address":{
             "name":{
                "first_name":"John",
                "middle_name":"Carter",
                "last_name":"Doe"
             },
             "full_address":"3339 Maryland Avenue, Largo, Florida",
             "selected_type":[
                "id_card"
             ],
             "supported_types":[
                "id_card",
                "bank_statement"
             ]
          }
       },
       "info":{
          "agent":{
             "is_desktop":true,
             "is_phone":false,
             "useragent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36
                                                (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
             "device_name":"Macintosh",
             "browser_name":"",
             "platform_name":"OS X - 10_14_0"
          },
          "geolocation":{
             "host":"212.103.50.243",
             "ip":"212.103.50.243",
             "rdns":"212.103.50.243",
             "asn":"9009",
             "isp":"M247 Ltd",
             "country_name":"Germany",
             "country_code":"DE",
             "region_name":"Hesse",
             "region_code":"HE",
             "city":"Frankfurt am Main",
             "postal_code":"60326",
             "continent_name":"Europe",
             "continent_code":"EU",
             "latitude":"50.1049",
             "longitude":"8.6295",
             "metro_code":"",
             "timezone":"Europe/Berlin"
          }
       },
       "additional_data":{
          "document":{
             "proof":{
                "height":"183",
                "country":"United Kingdom",
                "authority":"HMPO",
                "last_name":"Doe",
                "first_name":"John",
                "issue_date":"2018-01-31",
                "expiry_date":"2028-01-30",
                "nationality":"BRITISH CITIZEN",
                "country_code":"GBR",
                "document_type":"P",
                "place_of_birth":"BRISTOL",
                "document_number":"GB1234567",
                "personal_number":"12345678910",
                "dob":"1978-03-13",
                "gender":""
             }
          }
       }
    }


verification.declined
In case of a declined verification a “verification.declined” status is returned. This event also
refers to the declined reason. Both HTTP and callback responses are returned for this event.

A response sample is provided below for clarification;

```

    {
       "reference":"95156124",
       "event":"verification.declined",
       "error":"",
       "verification_result":{
          "document":{
             "name":0,
             "dob":1,
             "expiry_date":1,
             "issue_date":1,
             "document_number":1,
             "document":null
          },
          "address":{
             "name":null,
             "full_address":null
          }
       },
       "verification_data":{
          "document":{
             "name":{
                "first_name":"John",
                "middle_name":"Carter",
                "last_name":"Doe"
             },
             "dob":"1978-03-13",
             "issue_date":"2015-10-10",
             "expiry_date":"2025-12-31",
             "gender":"M""document_number":"1456-0989-5567-0909",
             "selected_type":[
                "id_card"
             ],
             "supported_types":[
                "id_card",
                "driving_license",
                "passport"
             ]
          },
          "address":{
             "name":{
                "first_name":"John",
                "middle_name":"Carter",
                "last_name":"Doe"
             },
             "full_address":"3339 Maryland Avenue, Largo, Florida",
             "selected_type":[
                "id_card"
             ],
             "supported_types":[
                "id_card",
                "bank_statement"
             ]
          }
       },
       "info":{
          "agent":{
             "is_desktop":true,
             "is_phone":false,
             "useragent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36
                                            (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
             "device_name":"Macintosh",
             "browser_name":"",
             "platform_name":"OS X - 10_14_0"
          },
          "geolocation":{
             "host":"212.103.50.243",
             "ip":"212.103.50.243",
             "rdns":"212.103.50.243",
             "asn":"9009",
             "isp":"M247 Ltd",
             "country_name":"Germany",
             "country_code":"DE",
             "region_name":"Hesse",
             "region_code":"HE",
             "city":"Frankfurt am Main",
             "postal_code":"60326",
             "continent_name":"Europe",
             "continent_code":"EU",
             "latitude":"50.1049",
             "longitude":"8.6295",
             "metro_code":"",
             "timezone":"Europe/Berlin"
          }
       },
       "declined_reason":"Name on the document doesn't match",
       "declined_codes":[
          "SPDR07",
          "SPDR06",
          "SPDR23"
       ],
       "additional_data":{
          "document":{
             "proof":{
                "height":"183",
                "country":"United Kingdom",
                "authority":"HMPO",
                "last_name":"Doe",
                "first_name":"John",
                "issue_date":"2018-01-31",
                "expiry_date":"2028-01-30",
                "nationality":"BRITISH CITIZEN",
                "country_code":"GBR",
                "document_type":"P",
                "place_of_birth":"BRISTOL",
                "document_number":"GB1234567",
                "personal_number":"12345678910",
                "dob":"1978-03-13",
                "gender":"M"
             }
          }
       }
    }


verification.status.changed
The status of a verification can be changed from the back office. From “Accepted” to “Declined” and
vice versa. In case the verification status is changed the client is notified through the callback URL. In
this case, no additional information is returned to the callback URL except the updated event.

```
    {
       "reference":"17374217",
       "event":"verification.status.changed"
    }

request.deleted
This event implies that the verification data has been deleted. The data once deleted from the back-
office also updates the status on the callback URL.

A sample response for a deleted verification is given below;

```

    {
       "reference":"17374217",
       "event":"request.deleted"
    }

request.recieved
This event states that the verification request has been received and is under processing. This event
only occurs for off-site verification when the request is sent to Shufti for processing.

```
    {
       "reference":"17374217",
       "event":"request.received",
       "email":"johndoe@example.com",
       "country":"UK"
    }

```
