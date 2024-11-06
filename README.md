# Schwab Tokens Generator

### **DESCRIPTION**

- This program allows you to obtain access and refresh tokens via OAuth through the Schwab API. This uses the Eel library for the GUI.
- Originally developed for TD Ameritrade to be used in conjunction with a Python trading script and web app, run from a cloud server like PyAnywhere.
  - The trading script may be run on a local machine, but the web app requires the cloud server, to my knowledge.
  - Original TDA-Token script: https://github.com/TreyThomas93/TDA-Token
  - Original TDA Trading bot: https://github.com/TreyThomas93/python-trading-bot-with-thinkorswim
  - Web App Server (run on PyAnywhere): https://github.com/TreyThomas93/tos-python-web-app-server
  - Web App (run on local machine, I believe): https://github.com/TreyThomas93/tos-python-bot-web-app
- User details are saved in MongoDB. Create a database named "**Api_Trader**", and **place access URI in config.env**. See https://www.MongoDB.com
  - Create an Atlas cluster and app. When viewing Clusters, click "Connect," and then "Drivers."
  - Mongo access URI is "connection string" listed near the bottom of the popup.
- PushSafer is used to send notifications to your device. See https://www.PushSafer.com
  - If you don't want these notifications, you may change the bot trading code to skip them. This script saves a default value in the user object regardless.
- Due to differences between TD Ameritrade and Schwab API functionality, the structure of the user dictionary is different from before.
  - See **user_object.py** for new structure. TDA trading bot has not (yet) been re-written for Schwab, but if you do so, new user structure must be used.
- **NOTE:** If you previously used these scripts for TD Ameritrade, your existing user account will be modified by this script to the new dictionary structure.

### **DEPENDENCIES**

---
> [packages]

- python-dotenv = "*"
- eel = "*"
- python-dateutil = "*"
- pymongo = "*"
- certifi = "*"
- selenium = "*"
- undetected-chromedriver = "*"
- requests = "*"

> [requires]

- python_version = "3.10"
  - This may run with older versions. Original script for TDA was developed with Python 3.8. This one was developed and tested with Python 3.10.
  - I've thought about using "3" to cover any Python 3 version, but I have no plans to test on all Python 3+ releases, and I know 3.10 works.

### **HOW IT WORKS**

---

- The purpose of this program is to obtain access and refresh tokens, and available account numbers and hashes from Schwab, and store that information in your MongoDB database.

- This program uses the Eel library to generate a GUI to make it easier to insert user info.

- Additionally, the undetected-chromedriver allows the script to automate most of the checkboxes and buttons during the login process.

- After the script logs you in, Schwab will send a code to your cellphone for two-factor authentication. You must manually enter the code that is sent via text message, AND press <enter> OR click the "Login" button. You will have **60 seconds** to do so before the script's automation will stop working properly.

- You are going to need to connect to the MongoDB Api_Trader database that you created in your cluster. **You will need to store your MongoDB URI** in a **config.env** file, stored in the root folder of the program.

#### **Create a Schwab API App**
- Navigate to https://developer.schwab.com and create an account. This is different from your Schwab brokerage account.

- Once registered, log in, and then click the Create App button.

- When choosing an API Product, it is uncertain what the difference is between the two options, but "Accounts and Trading Production" is recommended.

- Use "120" for Order Limit (this is for order-related requests).

- Enter an App Name; this can be whatever you want to call it. Enter a description so that the Schwab app approver knows what you want the app for.

- Enter a Callback URL. "Localhost" **cannot** be used. https://127.0.0.1:8282 (no trailing slash) works wonderfully.

- Once you complete the app request, the app status will be "Approved - Pending." This is misleading; it should be read as, "pending approval."

- You must wait for the app status to be "Ready For Use" to properly utilize the Schwab API and access your account(s) and place trades.

- From the Apps Dashboard, click on "View Details" for your app.

- At the bottom are the "App Key" and "Secret." These are your "App Key / Client ID" and "App Secret" which are used to obtain access and refresh tokens.

#### **Start the program**

- Run the **main.py** script. A "pipenv" virtual environment is recommended, utilizing the pipfile to install required packages.

- A browser window will appear with an "Add User" button at the top right, and any existing users will be displayed below and to the left.

#### **Add or Edit/Update User**

- If you click on the **Add User button** or a **User card**, you will see a page with the fields listed below.
  - "Add User" will pre-populate the fields with some default values. "Name" must be changed before saving.
  
- **Name** - This is the user's name

- **Device ID** - This is the device id for the Pushsafer API. This id is what allows you to push notifications from the program to your phone or any other device.

- **App Key / Client ID** - Required to obtain tokens. This is the app key created when you create an app in the Schwab Developers site.

- **App Secret** - Required to obtain tokens. This is the secret for your app, which you obtain from the Schwab Developers site.

- **Callback URL** - Required to obtain tokens. **Use the SAME callback URL that you used when you created the app on the Schwab Developers site.**

- **Scope** - "api": Retrieved from API. Used by API to ensure correct Access Token is used.

- **Token Type** - "Bearer": Retrieved from API. Used by API to ensure correct Access Token is used.

- **Access Token** - Retrieved from API. Replaces username & password to access your account information via the API.

- **Access Expiration** - Retrieved from API. Should be 30 minutes after it is generated.
  - If your Schwab app is "Approved - Pending," and not "Ready for Use", you may receive an Access Token good for 1 hour, but no Refresh Token.

- **Refresh Token** - Retrieved from API. Used by your trading script to refresh the Access Token when it expires.

- **Refresh Token Expiration** - 7 days after token generation. Use this script to obtain a new Refresh Token every week.

- **Accounts** - List of accounts in user collection of MongoDB. After token generation, accounts which your app has access to will be listed here.
  - **Archive** - Any old accounts in the user collection (i.e., from TD Ameritrade) which are no longer valid will be marked as "Archived." Past trades on these accounts will remain in your MongoDB collections unless you delete them from MongoDB.
  - **Active** - Your trading script should only trade Active accounts. Inactive accounts may be valid accounts, but your script shall ignore them.
  - **Live/Paper Trading** - Your trading script should use this to determine if trades on this account are real (live), or use play (paper) money for testing.
  - **Account Number** - Schwab brokerage Account Number
  - **Account Hash** - The Schwab API uses a hash of the account number, and not the number itself, to identify which account you are accessing.

#### **Save, Update Tokens & Accounts**

- When you click the above-named button, your user information will be saved, and a popup window will display with the following fields:

- **Username** - This is the username for your Schwab brokerage account – not developer account.

- **Password** - This is the password for your Schwab brokerage account.

- **Confirm Password** - Confirm the password you entered above. The passwords much match.
  - Username and encrypted password hash are saved in the user object, to be used as credentials if you use the web app.

#### **After Submission**

- After you submit the form, another browser will display and automatically input the username and password, and log into Schwab.

- If successful, it will ask you to input a two-factor authentication code that gets sent to your cellular phone.

- You have **60 seconds** to **enter the code** and **press the "Enter" key OR click the "Login" button**, or else the script will not function properly.

- The script's automation will continue after you press the "Enter" key or the "Login" button.

- Your tokens will be generated and automatically inserted in your MongoDB Api_Trader database in the "users" collection.

- The second browser will close, and you will return to the original browser with the "Edit Schwab User" page.

- Tokens, expiration dates, and accounts which are available to the App will be displayed.

- You may now close this browser and run your trading bot script.

- Run this script again in 7 days to obtain a new Refresh Token.
