
Schwab_user = {
    "_id": "New",
    "Name": "User's Name",
    "api_application": {
        "appKey": "ClientID/appKey from Schwab Dev",
        "appSecret": "appSecret from Schwab Dev",
        "callbackURL": "https://127.0.0.1:8182",
        "token": {
            "access_expiry": 1731286143,  # seconds since epoch,
            "access_token": "coded fleeting passport",
            "refresh_token": "coded phoenix catalyst",
            "token_type": "Bearer",
            "scope": "api",
            "refresh_expiry": 1731890943,  # seconds since epoch
        }
    },
    "Accounts": {
        "Account Number": {
            "Active": True,
            "account_hash": "account hash code",  # default: None
            "Account_Position": "Paper",
            "Archive": False
        },
        "Another AcctNum": {
            "Active": True,
            "account_hash": "another hash code",  # default: None
            "Account_Position": "Paper",
            "Archive": False
        }
    },
    "push_safer": {
        "deviceID": "from PushSafer"
    },
    "Username": "My voice is my passport",
    "Password": "Verify me"  # Setec Astronomy might come knocking. Shh!
}
