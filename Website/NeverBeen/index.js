
const NeverBeenAPI = "http://134.53.116.212:8000";

// Functions to perform when the page loads
function onload() {
    verifyAccount();
    showLoginButton();
}
    
// Create a function that shows the "Logout" button when the user is logged in
// If the user is not logged in, then the "Login" button is shown instead
// This function is called when the page loads
function showLoginButton () {
    // Check if the user is logged in
    var access_token = localStorage.getItem("access_token");
    console.log(access_token);
    if(access_token != null){
        // The user is logged in
        // Show the "Logout" button
        document.getElementById("loginButton").style.display = "none";
        document.getElementById("logoutButton").style.display = "block";
    } else {
        // The user is not logged in
        // Show the "Login" button
        document.getElementById("loginButton").style.display = "block";
        document.getElementById("logoutButton").style.display = "none";
    }
}

// Function that logs the user out when clicking the "Logout" button
function logout() {
    // Remove the access token from local storage
    localStorage.removeItem("access_token");
    // Show popup message to the user that they have been logged out
    Swal.fire({
        title: "Success!",
        text: "You have been logged out.",
        icon: "success",
        showConfirmButton: true
    }).then(function () {
        // Reload the page so that the user is logged out
        window.location.reload();
    });
}

// Detect if a token parameter exists in the current URL and if it does, then 
// call the "/verifyAccount" API endpoint in the NeverBeen API with the token as the response body
// If the token is valid, then the user is logged in and the user is redirected to the home page
// If the token is invalid, then the user is redirected to the login page
// If the token is missing, then the user is redirected to the login page
// If the user is already logged in, then the user is redirected to the home page
// If the user is not logged in, then the user is redirected to the login page
function verifyAccount() {
    const token = getUrlParameter("token");
    console.log(token);
    if (token) {
        const XHR = new XMLHttpRequest();
        XHR.open("post", NeverBeenAPI + "/verifyAccount");
        XHR.setRequestHeader("Content-type", "application/json");
        XHR.send(JSON.stringify({
            "token": token
        }));
        XHR.onreadystatechange = function () {
            if (this.readyState == 4 && this.status == 200) {
                // The token was valid
                // Store the token in local storage so that the user can be logged in automatically
                localStorage.setItem("access_token", token);
                // Show the user a sucess popup message
                Swal.fire({
                    title: "Success!",
                    text: "Your account has been verified.",
                    icon: "success",
                    showConfirmButton: true
                }).then(function () {
                    // Redirect the user to the home page
                    window.location.href = "index.html";
                });
            } else if (this.readyState == 4 && this.status == 400) {
                // The token was invalid
                // Tell the user that the token was invalid
                Swal.fire({
                    title: "Error!",
                    text: "The token was invalid. Please try again.",
                    icon: "error",
                    showConfirmButton: true
                }).then(function () {
                    // Redirect the user to the login page
                    window.location.href = "login.html";
                });
            }
        }
    } else {
        // The token was missing
        // Do nothing
    }
}

// Create a function "getUrlParameter" that takes in a parameter name and returns the value of the parameter
// This function is used to get the token from the URL
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

