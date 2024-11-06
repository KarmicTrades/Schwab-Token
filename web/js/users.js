
document.addEventListener("DOMContentLoaded", function () {
  // When page loads, fetch list of users

  eel.call_users();
});

eel.expose(response);
function response(response) {
  // Alert users on errors or successes

  if (response["error"]) {
    alert(response["error"]);
    return;
  } else alert(response["success"]);

  // Refresh the user list in case something changed
  eel.call_users();
}

eel.expose(fetch_users);
function fetch_users(users) {
  // Creates user cards from user list passed to Javascript from Python

  // CREATE CARD ELEMENTS FOR USERS
  let users_container = document.querySelector("#users-container");

  elements = "";

  users.forEach(user => {
    // We want to know when the Refresh Token expires
    // Convert seconds since epoch to milliseconds since epoch
    let refresh_expires = 1000 *
      user["api_application"]["token"]["refresh_expiry"];

    let name = user["Name"];

    let refresh_exp = new Date(refresh_expires).toDateString();

    let current_date = new Date().getTime();

    let expired = false;

    // IF CURRENT DATE IS PAST REFRESH EXP
    if (refresh_expires < current_date) expired = true;

    // Checks if user has active accounts or not
    const accounts = Object.keys(user["Accounts"]);

    let inactive = true;

    accounts.forEach(acct => {

      if (user["Accounts"][acct]["Active"]) {

        inactive = false;
      }

    })

    // Create the user card
    elements += `
      <div class="card">
        <h5>Name: ${name}</h5>

        <div class="inner-div">
          <label>Refresh Token Expires: ${refresh_exp}</label>
        </div>

        <div class="${(inactive || expired) ? "expired" : "not-expired"}">
          <h1>${inactive ? "INACTIVE" : "EXPIRED"}</h1>
        </div>

        <a href="edit.html?name=${name}" class="card-link"></a>
      </div>
    `;
  });

  users_container.innerHTML = elements;
}
