document.addEventListener("DOMContentLoaded", function () {

  // Retrieve the user from MongoDB and display user info
  eel.call_user(get_parameter_by_name('name'));

  // GET BUTTONS
  let exit_button = document.querySelector("#no-save-exit-btn");
  let save_user_button = document.querySelector("#save-user-btn");
  let update_tokens_button = document.querySelector("#update-tokens-btn");
  let update_user_button = document.querySelector("#update-user-btn");
  let login_save_button = document.querySelector("#login-save-btn");
  let exit_login_popup = document.querySelector("#exit-login-popup");

  // LISTEN FOR CLICKS AND CALL FUNCTIONS
  // Exit and go back to user list
  exit_button.addEventListener("click", exit_user); // Don't save changes
  save_user_button.addEventListener("click", save_and_exit); // Save changes

  // Open or close username/password popup
  update_user_button.addEventListener("click", open_popup); // Saves user first
  exit_login_popup.addEventListener("click", close_popup); // Cancels the login

  // FETCH TOKENS & ACCOUNTS
  update_tokens_button.addEventListener("click", update_tokens); // Saves after
  login_save_button.addEventListener("click", update_user_and_tokens); // Saves after
});

function get_parameter_by_name(name, url) {
// Gets name of user from parameters passed to webpage in URL
// I didn't take time to understand how it works, but I found it in
// several places online as a URL parser to obtain parameters

  if (!url) url = window.location.href;
  name = name.replace(/[\[\]]/g, '\\$&');
  var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)'),
      results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return '';
  return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

function exit_user() {
// Go back to user list without saving changes

  window.location.href = "users.html";
}

function collect_form_data(form_id) {
// Compiles data from input fields into a dictionary

  var inputs = new FormData(document.getElementById(form_id));

  var data = {};

  for (var ipt of inputs) {

    data[ipt[0]] = ipt[1];

  }

  return data;
}

function save_the_user() {
// Sends user info to Python for saving to MongoDB

  var user_data = collect_form_data("user_form");

  if (user_data["Name"] === "User's Name") {

    alert("Error: A Name Must Be Entered For The User.");

    return "Error";
  }

  eel.save_user(user_data);

  // If we've saved the user, then MongoDB now has "Name"
  // "old_name" must now reflect the "Name" that's in MongoDB
  const old_name_element = document.getElementById("old_name");

  old_name_element.value = user_data["Name"];

  return "Success";
}

function save_and_exit() {
// Saves. And exits.

  // Performs save function if no error
  if (save_the_user() === "Error") {
    return;
  }

  window.location.href = "users.html";
}

function open_popup(e) {
// Opens the login popup after saving the user

  if (e.target.id === "update-user-btn") {

    // Performs save function if no error
    if (save_the_user() === "Error") {
      return;
    }

    document.querySelector("#login-popup").style.display = "block";
  }
}

function close_popup(e) {
// If we "Exit" or "Submit" the popup box, close the popup

  if (
    e.target.id === "exit-login-popup" ||
    e.target.id === "login-save-btn"
  ) {

    document.querySelector("#login-popup").style.display = "none";
  }
}

function update_tokens(e) {
// Send the user data to Python to fetch tokens and accounts

  e.preventDefault();

  // Collect user info
  var user_data = collect_form_data("user_form");

  // Send user data for Python to contact Schwab for tokens and accounts
  eel.fetch_tokens_and_accounts(user_data);

  // Refresh "Edit User" page to display new tokens and accounts
  eel.call_user(user_data["Name"]);
}

function update_user_and_tokens(e) {
// Send the user data to Python to fetch tokens and accounts

  e.preventDefault();

  var elements = e.target.parentElement;

  var login_data = {};

  var password = null;

  // Make sure there's a Username *and* password
  for (var ipt of elements) {

    if (ipt.value === "") {
      alert("Error: All Fields Must Have A Value.");

      return;
    }

    // Password and Confirm Password MUST match before we attempt to login
    if (ipt.name === "Password") password = ipt.value;

    if (ipt.name === "Confirm_Password") {
      if (ipt.value !== password) {
        alert("Passwords Do Not Match.");

        return;
      }

      continue;
    }

    if (ipt.value === "Submit") continue;

    login_data[ipt.name] = ipt.value;
  }

  // Collect user info and merge with login info
  var user_data = collect_form_data("user_form");

  var new_form_data = Object.assign({}, login_data, user_data);

  // Send user data for Python to contact Schwab for tokens and accounts
  eel.fetch_tokens_and_accounts(new_form_data);

  // Close that popup
  close_popup(e);

  // Refresh "Edit User" page to display new tokens and accounts
  eel.call_user(new_form_data["Name"]);
}

eel.expose(response);
function response(response) {
// Issues a popup dialog to alert user of errors or responses

  if (response["error"]) {
    alert(response["error"]);
    return;
  } else alert(response["success"]);

}

function check_pass() {
// Make sure the Password and Confirm Password match when user is typing them in
// If they don't match, display a warning

  let password_conf = document.getElementById('Confirm_Password').value;

  let pass = document.getElementById('Password').value;

  element = document.querySelector('.password_warning');

  if (password_conf != pass) {

    element.style.visibility = 'visible';

  } else {

    element.style.visibility = 'hidden';
  }
}

eel.expose(fetch_user);
function fetch_user(user) {
// We're not fetching the user so much as we're displaying the fetched user info

  // Initialize
  let refresh_expired = false;

  let access_expired = false;

  if ("Passcode" in user) {

    if (user["Passcode"] !== "Too many secrets") {

      let update_tokens_btn = document.getElementById("update-tokens-btn")
      update_tokens_btn.style.display = "inline-block";
    }
  }

  // Convert seconds since epoch to milliseconds since epoch
  let refresh_expires = 1000 *
    user["api_application"]["token"]["refresh_expiry"];

  let access_expires = 1000 *
    user["api_application"]["token"]["access_expiry"];

  // Convert milliseconds to datetime string so user can read it
  let refresh_expiration = new Date(refresh_expires).toLocaleString();

  let access_expiration = new Date(access_expires).toLocaleString();

  let current_date = new Date().getTime();

  // If expiration dates are in the past
  if (refresh_expires < current_date) refresh_expired = true;

  if (access_expires < current_date) access_expired = true;

  // CREATE ELEMENTS FOR USERS
  elements = ""; // Initialize

  // Fill elements with user info to display
  elements += `
    <form class="user_inputs" id="user_form">
      <input
        type="hidden" id="old_name" name="old_name"
        value="${user["Name"]}"
      />
      <label for="Name">Name:</label>
      <input
        type="text" id="Name" name="Name"
        value="${user["Name"]}"
      />
      <br><br>
      <label for="Device_ID">PushSafer Device ID:</label>
      <input
        type="text" id="Device_ID" name="Device_ID"
        value="${user["push_safer"]["deviceID"]}"
        size=15
      />
      <br><br>
      <label for="Client_ID">App Key / Client ID of API Schwab app:</label>
      <input
        type="text" id="Client_ID" name="Client_ID"
        value="${user["api_application"]["appKey"]}"
        size=50
      />
      <br>
      <label for="App_Secret">App Secret of API Schwab app:</label>
      <input
        type="text" id="App_Secret" name="App_Secret"
        value="${user["api_application"]["appSecret"]}"
        size=50
        class="gap_me"
      />
      <br>
      <label for="Callback_URL">Callback URL of API Schwab app:</label>
      <input
        type="text" id="Callback_URL" name="Callback_URL"
        value="${user["api_application"]["callbackURL"]}"
        size=50
        class="gap_me"
      />
      <br><br>
      <b>
      <p>===================================================================</p>
      <p>THE FOLLOWING INFORMATION IS RETRIEVED FROM SCHWAB.</p>
      <p>YOU MAY ENTER EXISTING INFO, BUT IT IS REFRESHED WHEN RETRIEVING ACCOUNTS.</p>
      </b>
      <br>
      <label for="token_scope">Token Scope:</label>
      <input
        type="text" id="token_scope" name="token_scope"
        value="${user["api_application"]["token"]["scope"]}"
        size=20 class="gap_me"
      />
      <br>
      <label for="token_type">Token Type:</label>
      <input
        type="text" id="token_type" name="token_type"
        value="${user["api_application"]["token"]["token_type"]}"
        size=20 class="gap_me"
      />
      <br>
      <label for="token_access">Access Token:</label>
      <textarea
        type="text" id="token_access" name="token_access"
        cols=75 rows=2
        ${access_expired ? "class='expired_border'" : "class='gap_me'"}
      >${user["api_application"]["token"]["access_token"]}</textarea>
      <br>
      <label for="Access_Expiration">Access Token Expiration:</label>
      <input
        type="text" id="Access_Expiration" name="Access_Expiration"
        value="${access_expiration}"
        size=20
        ${access_expired ? "class='expired_border'" : "class='gap_me'"}
      />
      <br>
      <label for="token_refresh">Refresh Token:</label>
      <textarea
        type="text" id="token_refresh" name="token_refresh"
        cols=75 rows=3
        ${refresh_expired ? "class='expired_border'" : "class='gap_me'"}
      >${user["api_application"]["token"]["refresh_token"]}</textarea>
      <br>
      <label for="Refresh_Expiration">Refresh Token Expiration:</label>
      <input
        type="text" id="Refresh_Expiration" name="Refresh_Expiration"
        value="${refresh_expiration}"
        size=20
        ${refresh_expired ? "class='expired_border'" : "class='gap_me'"}
      />
      <br><br>
      <table>
        <caption><b>Accounts</b></caption>
        <tr>
          <th>Archived</th>
          <th>Active</th>
          <th>Live/Paper Trading</th>
          <th>Account Number</th>
          <th>Account Hash</th>
        </tr>
  `;

  // Accounts are listed as well
  let accounts = user["Accounts"];

  user["sort_order"].forEach(acct => {

    let live = accounts[acct]["Account_Position"] === "Live";
    let archived = accounts[acct]["Archive"]

    elements += `
        <tr>
          <td class="archive_cell">
            <input
              type="radio" id="archive_${acct}" name="archive_${acct}"
              value="Archived"
              ${archived ? "" : "hidden"} ${archived ? "checked" : ""}
            /></td>
          <td class="active_cell">
            <input type="checkbox" id="status_${acct}s" name="status_${acct}"
            ${accounts[acct]["Active"] ? "checked" : ""}
            ${archived ? "hidden" : ""}
          /></td>
          <td class="cells">
            <input type="radio" id="live_${acct}" name="live_${acct}"
            value="Live"
            ${live ? "checked" : ""} ${archived ? "hidden" : ""}
            />
            <label for="live_${acct}" ${archived ? "hidden" : ""}>
            Live Trading
            </label><br>
            <input type="radio" id="paper_${acct}" name="live_${acct}"
            value="Paper"
            ${live ? "" : "checked"} ${archived ? "hidden" : ""}
            />
            <label for="paper_${acct}" ${archived ? "hidden" : ""}>
            Paper Trading
            </label>
          </td>
          <td class="account_cell">
            ${acct}
          </td>
          <td class="cells">
            <textarea type="text" id="account_hash" name="hash_${acct}"
            cols=40 rows=2 ${archived ? "hidden" : ""}
            >${accounts[acct]["account_hash"]}</textarea>
          </td>
        </tr>
    `;
  });

  elements += `
      </table>
      <p class="note">
      Note: Archived accounts are inaccessible to this API app.
      <br>
      For as long as this is the case, they are inactive and cannot be changed.
      </p>
    </form>
  `;

  // Insert user info elements into the user-container of the html page
  let user_container = document.querySelector("#user-container");

  user_container.innerHTML = elements;
}
