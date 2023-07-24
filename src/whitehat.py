from src.models.registration import Registration

def create_account(registration: Registration):
    account_id = create_account_in_whg(registration)
    manually_approve_kyc(account_id)

    # Send loyalty card number as the username
    pass
    # Hit the API to create the account
    # Then hit the API again to "manually approve" the KYC.