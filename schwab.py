import urllib.parse as up
import undetected_chromedriver as uc
import time
import requests
import traceback
import string
import random

TOKEN_ENDPOINT = 'https://api.schwabapi.com/v1/oauth/token'

AUTHORIZATION_ENDPOINT = 'https://api.schwabapi.com/v1/oauth/authorize'

ACCTS_ENDPOINT = "https://api.schwabapi.com/trader/v1/accounts/accountNumbers"

DEFAULT_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
}

UNICODE_ASCII_CHARACTER_SET = string.ascii_letters + string.digits


def generate_token(length=30, chars=UNICODE_ASCII_CHARACTER_SET):
    # Generates "state" to be used in OAuth process to mitigate CSRF attacks

    rand = random.SystemRandom()

    return ''.join(rand.choice(chars) for _ in range(length))


def initialize_tokens(form_data):
    # Starts the OAuth process to obtain tokens
    # noinspection PyBroadException

    try:
        # Schwab has been restricting automation, so use undetected-chromedriver
        # instead of regular chromedriver
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option(
            "prefs", {"credentials_enable_service": False,
                      "profile.password_manager_enabled": False})

        driver = uc.Chrome(options=options, use_subprocess=False)

        client_id = form_data["Client_ID"]

        app_secret = form_data["App_Secret"]

        redirect_uri = form_data["Callback_URL"]

        state = generate_token()

        url = AUTHORIZATION_ENDPOINT + \
            '?response_type=code' + \
            '&client_id=' + up.quote(client_id) + \
            '&redirect_uri=' + up.quote(redirect_uri) + \
            '&scope=' + up.quote(form_data["token_scope"]) + \
            '&state=' + up.quote(state)

        driver.get(url)

        # How long to wait for element id to be found
        driver.implicitly_wait(60)

        # Log user in
        user_box = driver.find_element("id", 'loginIdInput')

        password_box = driver.find_element("id", 'passwordInput')

        user_box.send_keys(form_data["Username"])

        # To avoid Schwab catching-on to the automation...
        # Sleep times are set to mimic typical manual user responses
        time.sleep(2)

        password_box.send_keys(form_data["Password"])

        time.sleep(1)

        # btnLogin : "Login" button
        driver.find_element("id", 'btnLogin').click()

        # Within 60 seconds...
        # User must enter SMS Security code
        # User must then press <Enter> key or click the 'Login' button

        # acceptTerms : "Accept" checkbox
        driver.find_element("id", 'acceptTerms').click()

        time.sleep(2)

        # submit-btn : "Continue" button
        driver.find_element("id", 'submit-btn').click()

        time.sleep(3)

        # agree-modal-btn- : "Accept" button
        driver.find_element("id", 'agree-modal-btn-').click()

        time.sleep(2)

        # submit-btn : "Continue" button
        driver.find_element("id", 'submit-btn').click()

        time.sleep(3)

        # cancel-btn : "Done" button
        driver.find_element("id", 'cancel-btn').click()

        # Wait for callback response with code to retrieve tokens
        while True:

            # noinspection PyBroadException
            try:

                uri = driver.current_url

                code = up.unquote(uri.split('code=')[1])

                if code != '':

                    break

                else:

                    time.sleep(2)

            except:  # noqa: E722

                pass

        driver.close()

        query = up.urlparse(uri).query

        params: dict = dict(up.parse_qsl(query))

        # We need the code to fetch tokens
        if 'code' not in params:
            error_text = "Missing code from redirect uri - " + \
                         "unable to authenticate"

            return {"error": error_text}

        # "state" returned to us must match what we sent to mitigate CSRF attack
        params_state = params.get('state')

        if state and params_state != state:
            return {"error": "Mismatched state - unable to authenticate"}

        # Now, we finally fetch the tokens
        resp = requests.post(TOKEN_ENDPOINT, headers=DEFAULT_HEADERS,
                             auth=(client_id, app_secret),
                             data={'grant_type': 'authorization_code',
                                   'code': params["code"],
                                   'client_id': client_id,
                                   'redirect_uri': redirect_uri})

        # Successful response status is 200
        if resp.status_code != 200:
            error_text = "Unexpected response code (" + \
                         str(resp.status_code) + ") - unable to authenticate"

            return {"error": error_text}

        response = resp.json()

        # Send the username/password to be saved in user dictionary
        response["Username"] = form_data["Username"]

        response["Password"] = form_data["Password"]

        return response

    except Exception:

        return {"error": traceback.format_exc()}


def get_accounts(access_token, token_type):
    # Gets list of accounts accessible to the app, and their hashes
    # Account hashes are used by API to access account data, not account number

    # We use our freshly-fetched Access Token to get account data
    token = {"Authorization": f"{token_type} {access_token}"}

    header = {**DEFAULT_HEADERS, **token}

    resp = requests.get(ACCTS_ENDPOINT, headers=header)

    # Successful response status is 200
    if resp.status_code != 200:
        error_text = "Unexpected response code (" + \
                     str(resp.status_code) + ") - unable to get account numbers"

        return {"error": error_text}

    return resp.json()
