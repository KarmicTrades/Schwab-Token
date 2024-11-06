import eel
from schwab import initialize_tokens, get_accounts
from encrypt_password import encrypt_password
from mongo import MongoDB
from dateutil import parser
import time
import traceback


eel.init("web")

mongo = MongoDB()

mongo.connect_mongo()


def sort_accounts(accounts):
    # Sort accounts in groups: [not-archived: [active -> inactive]] -> archived

    # Re-order account fields and establish defaults, if field not found
    formatted_account = {}

    for acct in accounts.keys():

        formatted_account[acct] = {
            "Active": accounts[acct].get("Active", True),
            "account_hash": accounts[acct].get("account_hash"),  # default = None
            "Account_Position": accounts[acct].get("Account_Position", "Paper"),
            "Archive": accounts[acct].get("Archive", False)
        }

        # If there are account fields we don't control, add them
        formatted_account[acct] = {**formatted_account[acct],
                                   **accounts[acct]}

        # if account is archived, then it's inactive
        if formatted_account[acct]["Archive"]:
            formatted_account[acct]["Active"] = False

    # Initialize lists for sorting
    archive = []
    not_archive = []
    active = []

    for acct_num in formatted_account.keys():

        if formatted_account[acct_num]["Active"]:
            active.append(acct_num)

            # Save a few picoseconds by recording active accounts as active only
            continue

        # Inactive (not-traded) accounts:
        # all archived accounts are inactive
        if formatted_account[acct_num]["Archive"]:

            archive.append(acct_num)

        # inactive and not archived
        else:

            not_archive.append(acct_num)

    active.sort()
    not_archive.sort()
    archive.sort()

    # Create new dictionary and add accounts in sorted order
    # Accounts look like numbers, even though they're strings, so MongoDB sorts
    # them. I believe this is a new issue, but since we need these sorted for
    # visual pleasantness, we pass sort_order for when we display accounts to
    # edit the user data
    sorted_acct = {}
    sort_order = []

    for acct_num in active:
        sorted_acct[acct_num] = formatted_account[acct_num]
        sort_order.append(acct_num)

    for acct_num in not_archive:
        sorted_acct[acct_num] = formatted_account[acct_num]
        sort_order.append(acct_num)

    for acct_num in archive:
        sorted_acct[acct_num] = formatted_account[acct_num]
        sort_order.append(acct_num)

    return dict(sorted_acct), sort_order


def merge_accounts(old_accounts, new_accounts):
    # Merges two account dictionaries, giving preference to new data,
    # without sacrificing existing fields

    accounts = dict(new_accounts)

    for acct in old_accounts.keys():

        if acct in accounts.keys():
            old_accounts[acct] = {**old_accounts[acct], **accounts[acct]}

        accounts[acct] = old_accounts[acct]

    return accounts


def user_cleanup(user):
    # Cleans up user dictionary from older versions of this script

    user_keys = user.keys()

    user["cleaned"] = True

    if "api_application" in user_keys:

        api_app_keys = user["api_application"].keys()

        # If user dictionary is current version, don't clean it
        # Saves some CPU logic calls, and hopefully a millisecond or two
        if "token" in api_app_keys:
            user["cleaned"] = False

            return user

        # If user dictionary is previous version
        if "metadata_wrapped_token" in api_app_keys:

            wrapped_token = user["api_application"]["metadata_wrapped_token"]

            user["api_application"]["token"] = {}

            token = {
                "access_expiry": wrapped_token["token"]["expires_at"],
                "access_token": wrapped_token["token"]["access_token"],
                "refresh_token": wrapped_token["token"]["refresh_token"],
                "token_type": wrapped_token["token"]["token_type"],
                "scope": wrapped_token["token"]["scope"],
                "refresh_expiry": 604800 + wrapped_token["creation_timestamp"]
            }

            user["api_application"]["token"] = dict(token)

            del wrapped_token["creation_timestamp"]

            del_keys = ["expires_in", "token_type", "scope", "refresh_token",
                        "access_token", "id_token", "expires_at"]

            for del_key in del_keys:

                if del_key in wrapped_token["token"]:
                    del wrapped_token["token"][del_key]

            if not wrapped_token["token"]:
                del wrapped_token["token"]

            if not user["api_application"]["metadata_wrapped_token"]:
                del user["api_application"]["metadata_wrapped_token"]

        if "initialize_access" in user_keys:

            initial_keys = user["initialize_access"].keys()

            if "username" in initial_keys:
                user["Username"] = user["initialize_access"]["username"]

                del user["initialize_access"]["username"]

            if "password" in initial_keys:
                user["Password"] = user["initialize_access"]["password"]

                del user["initialize_access"]["password"]

            if not user["initialize_access"]:
                del user["initialize_access"]

    # Seconds since epoch time
    epoch_seconds = int(time.time())

    # Format user dictionary and set default values for new user
    new_user = {
        "_id": "New",
        "Name": "User's Name",
        "api_application": {
            "appKey": "ClientID/appKey from Schwab Dev",
            "appSecret": "appSecret from Schwab Dev",
            "callbackURL": "https://127.0.0.1:8182",
            "token": {
                "access_expiry": epoch_seconds,
                "access_token": "coded fleeting passport",
                "refresh_token": "coded phoenix catalyst",
                "token_type": "Bearer",
                "scope": "api",
                "refresh_expiry": epoch_seconds
            }
        },
        "Accounts": {},
        "push_safer": {
            "deviceID": "from PushSafer"
        },  # User won't see this unless they look for the default values
        "Username": "My voice is my passport",
        "Password": "Verify me"  # Setec Astronomy might come knocking. Shh!
    }

    # Merge user template above with existing user dictionary
    # "user" dictionary for a new user is empty, so default values are kept
    user = {**new_user, **user}

    # If user dictionary is original version, update old fields as necessary
    if "deviceID" in user_keys:
        device_id = user["deviceID"]

        user["push_safer"]["deviceID"] = device_id

        del user["deviceID"]

    if "ClientID" in user_keys:
        del user["ClientID"]

    if "Accounts" in user_keys:
        # sort_order is not needed here
        user["Accounts"], sort_order = sort_accounts(user["Accounts"])

    return user


@eel.expose
def save_user(form_data):
    # Saves the user to MongoDB

    # Convert datetime strings to datetime objects
    access_expiry_dt = parser.parse(form_data["Access_Expiration"])
    refresh_expiry_dt = parser.parse(form_data["Refresh_Expiration"])

    # Get epoch time in seconds of expiration dates
    access_expiry = int(access_expiry_dt.timestamp())
    refresh_expiry = int(refresh_expiry_dt.timestamp())

    # Properly format and fill-in user dictionary with form data
    new_user_data = {
        "Name": form_data["Name"],
        "api_application": {
            "appKey": form_data["Client_ID"],
            "appSecret": form_data["App_Secret"],
            "callbackURL": form_data["Callback_URL"],
            "token": {
                "access_expiry": access_expiry,
                "access_token": form_data["token_access"],
                "refresh_token": form_data["token_refresh"],
                "token_type": form_data["token_type"],
                "scope": form_data["token_scope"],
                "refresh_expiry": refresh_expiry
            }
        },
        "Accounts": {},
        "push_safer": {
            "deviceID": form_data["Device_ID"]
        },  # User has not yet entered login info
        "Username": "My voice is my passport",  # keeping Setec Astronomy at bay
        "Password": "Verify me"  # The cocktail party is just around the bend
    }

    accounts = {}

    keys = form_data.keys()

    # This looks confusing, but it's simple.
    # Element ids for accounts on form are as follows for account 123:
    # status_123 (active), hash_123, live_123 (account position), archive_123
    for field in keys:

        key = field.split("_")

        if key[0] == "live":
            accounts[key[1]] = {
                "Active": True if "status_" + key[1] in keys else False,
                "account_hash": form_data["hash_" + key[1]],
                "Account_Position": form_data[field],
                "Archive": True if "archive_" + key[1] in keys else False
            }

    new_user_data["Accounts"] = accounts

    # By this point in script, user's new name has already been entered.
    # We need to change old_name to Name, in case user was saved with new tokens
    # In case of new tokens, user returns to "edit user" screen.
    # If user clicks "Save User & Exit," then old_name MUST match Name in Mongo
    if form_data["old_name"] == "User's Name":

        old_name = form_data["Name"]

    # If existing user
    else:
        # Keep old_name, because that's the user we're modifying
        old_name = form_data["old_name"]

        # Retrieve existing user
        user = mongo.users.find_one({"Name": old_name})

        # Retrieve existing username and password
        if "Username" in user.keys():
            new_user_data["Username"] = user["Username"]

            new_user_data["Password"] = user["Password"]

        # If we have existing accounts, merge with new ones, if any
        if "Accounts" in user.keys():
            new_user_data["Accounts"] = merge_accounts(
                user["Accounts"], new_user_data["Accounts"])

        # Overwrite matching fields in user with data from new_user_data
        # Keep fields in user if none exist in new_user_data
        new_user_data = {**user, **new_user_data}

    # sort_order is not needed here
    new_user_data["Accounts"], sort_order = sort_accounts(
        new_user_data["Accounts"])

    # Save it to Mongo
    mongo.users.update_one(
        {"Name": old_name},
        {"$set": new_user_data},
        upsert=True
    )

    return


@eel.expose
def fetch_tokens_and_accounts(form_data):
    # Fetches tokens and accounts from Schwab API

    # noinspection PyBroadException

    try:
        # SEND DATA TO SCHWAB OBJECT TO GET TOKENS
        token_data = initialize_tokens(form_data)

        if "error" in token_data:
            # IF ERROR, THEN RETURN ERROR TO JS AND DISPLAY TO USER
            eel.response({"error": token_data["error"]})

            return

        # Current seconds since epoch time
        epoch_seconds = int(time.time())

        # Format token dictionary
        token = {
            "access_expiry": epoch_seconds + token_data["expires_in"],
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "token_type": token_data["token_type"],
            "scope": token_data["scope"],
            "refresh_expiry": epoch_seconds + 604800  # 7 days from current time
        }

        # SAVE TO MONGO.
        mongo.users.update_one(
            {"Name": form_data["Name"]},
            {"$set": {"api_application.token": token,
                      "Username": token_data["Username"],  # No more secrets
                      "Password": encrypt_password(token_data["Password"])}}
        )

        # Fetch account numbers and hashes from Schwab API
        accounts_data = get_accounts(token["access_token"], token["token_type"])

        if "error" in accounts_data:
            # IF ERROR, THEN RETURN ERROR TO JS AND DISPLAY TO USER
            eel.response({"error": accounts_data["error"]})

            return

        # Get user so that we can update accounts, keeping archived accounts in-tact
        user = mongo.users.find_one({"Name": form_data["Name"]})

        current_acct_nums = []

        if "Accounts" not in user.keys():
            user["Accounts"] = {}

        for acct in accounts_data:

            acct_num = acct["accountNumber"]

            current_acct_nums.append(acct_num)

            if acct_num not in user["Accounts"].keys():
                user["Accounts"][acct_num] = {}

            user["Accounts"][acct_num]["account_hash"] = acct["hashValue"]

            user["Accounts"][acct_num]["Archive"] = False

        # sort_order is not needed here
        user_accts, sort_order = sort_accounts(user["Accounts"])

        # If existing account not in current accessible account list, Archive it
        for acct in user_accts.keys():

            if acct not in current_acct_nums:
                user_accts[acct]["Archive"] = True

                user_accts[acct]["Active"] = False

        # SAVE TO MONGO.
        mongo.users.update_one(
            {"Name": form_data["Name"]},
            {"$set": {"Accounts": user_accts}},
        )

        action = "Tokens and Accounts retrieved!"

        eel.response({"success": action})

        return

    except Exception:
        # IF ERROR, THEN RETURN ERROR TO JS AND DISPLAY TO USER
        eel.response({"error": traceback.format_exc()})

        return


def is_inactive(user):
    # Checks if account is inactive. Used for sorting.

    inactive = True

    for account in user["Accounts"].keys():

        if user["Accounts"][account]["Active"]:
            inactive = False

            break

    return inactive


@eel.expose
def call_users():
    # FETCH ALL USERS AND SEND TO JS TO BE DISPLAYED

    users = [user for user in mongo.users.find()]

    new_users = []

    for user in users:

        # In previous version, "TDA_user" was near carbon-copy of original user.
        # That went away. Clean it and merge with new user dictionary.
        if "TDA_user" in user.keys():

            new_tda_user = user_cleanup(user["TDA_user"])

            del user["TDA_user"]

            new_tda_user_keys = new_tda_user.keys()

            if "Accounts" in new_tda_user_keys:

                # If TDA_user had Accounts, need to iterate through them to
                # keep fields we don't control. That is, if tda_user has a
                # field we're not aware of, we need to keep it
                if new_tda_user["Accounts"]:
                    user["Accounts"] = merge_accounts(
                        new_tda_user["Accounts"], user.get("Accounts", {}))

                # Remove Accounts from tda_user since we don't need it anymore
                del new_tda_user["Accounts"]

            # Delete these keys so that we don't write over current user data
            old_keys = ["_id", "Name", "Username", "Password",
                        "api_application", "push_safer"]

            for old_key in old_keys:

                if old_key in new_tda_user_keys:
                    del new_tda_user[old_key]

            # If user stored extra fields in user object, keep them
            if new_tda_user:
                user = {**user, **new_tda_user}

        # Now clean the merged/current user dictionary
        new_user = user_cleanup(user)

        new_users.append(new_user)

        # If we cleaned it, delete "cleaned" field and save user to Mongo
        if new_user["cleaned"]:
            del new_user["cleaned"]

            mongo.users.replace_one({"_id": new_user["_id"]}, new_user)

    # Users with no active accounts are sorted to display at end
    # Order of users in MongoDB is not changed
    new_users.sort(key=is_inactive)

    # Send the user list to javascript to display in browser
    eel.fetch_users(new_users)


@eel.expose
def call_user(user_name):
    # FETCH USER AND SEND TO JS TO BE DISPLAYED
    user = mongo.users.find_one({"Name": user_name})

    # Creates default values for new user
    if not user:
        user = {}

        user = user_cleanup(user)

    # Now, we use sort_order. Pass to "edit user" page.
    user["Accounts"], user["sort_order"] = sort_accounts(user["Accounts"])

    # Send to javascript to display user data
    eel.fetch_user(user)


if __name__ == '__main__':
    # Start the script/browser

    eel.start("users.html", size=(1024, 768), position=(0, 0))
