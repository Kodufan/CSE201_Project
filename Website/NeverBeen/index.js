
const NeverBeenAPI = "http://134.53.116.212:8000";

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
                // Now we need to redirect the user to the home page
                window.location.href = "index.html";
            } else if (this.readyState == 4 && this.status == 400) {
                // The token was invalid
                // Now we need to redirect the user to the login page
                window.location.href = "login.html";
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

// Call the verifyAccount() function when the page loads
window.onload = function () {
    verifyAccount();
}

