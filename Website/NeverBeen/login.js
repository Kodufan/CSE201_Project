
const NeverBeenAPI = "http://134.53.116.212:8000";

// Function used in tab switching
function tabSelect(event, tabName){
    // Declare all variables
    var i, tabcontent, tablinks;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(tabName).style.display = "block";
    event.currentTarget.className += " active";
}

// Check if "access_token" is in local storage
// If it is, check if the token is valid
// If it is valid, then the user is logged in and the user is redirected to the home page
// If it is invalid, remove the access token from local storage and redirect the user to the login page
// This is incomplete so far
var access_token = localStorage.getItem("access_token");
if(access_token != null){
    window.location.href = "index.html";
}

// Function that detects when the "Signup" form is submitted
// When the form is submitted, send the form information to the "/createUser" endpoint in the NeverBeen API
// If the user is successfully created, then the user is redirected to index.html
console.log(document.getElementById("Signup"));
document.getElementById("Signup").onsubmit = function(event){
    event.preventDefault();
    var username = document.getElementsByName("username")[0].value; // 1st instance of the username name
    var email = document.getElementsByName("email")[1].value; // 2nd instance of the email name
    var password = document.getElementsByName("rawPassword")[1].value; // 2nd instance of the rawPassword name
    var XHR = new XMLHttpRequest();
    XHR.open("post", NeverBeenAPI+"/createUser");
    XHR.setRequestHeader("Content-type", "application/json");
    XHR.send(JSON.stringify({
        "username": username,
        "email": email,
        "rawPassword": password
    }));
    XHR.onreadystatechange = function(){
        if(this.readyState == 4 && this.status == 201){ // 201 is the status code for "Created"
            // The user was successfully created
            // Show the user a success message
            Swal.fire({
                title: "Success!",
                text: "Your account has been created! Check your email to verify your account.",
                icon: "success",
                confirmButtonText: "Continue"
            }).then(function(){
                // Redirect the user to the home page
                window.location.href = "index.html";
            });
        } else {
            // The user was not created
            // Send error message to the user
            Swal.fire({
                title: "Error!",
                text: "There was an error creating your account."+this.responseText,
                icon: "error",
                confirmButtonText: "Continue"
            }).then(function(){
                // Refresh the login page
                window.location.href = "login.html";
            });
        }
    }
};


// Function that detects when the "Login" form is submitted
// When the form is submitted, send the form information to the "/login" endpoint in the NeverBeen API
// If the user is successfully created, then the user is redirected to index.html
console.log(document.getElementById("Login"));
document.getElementById("Login").onsubmit = function(event){
    event.preventDefault();
    var email = document.getElementsByName("email")[0].value; // 1st instance of the email name
    var password = document.getElementsByName("rawPassword")[0].value; // 1st instance of the rawPassword name
    var XHR = new XMLHttpRequest();
    XHR.open("post", NeverBeenAPI+"/login");
    XHR.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    console.log(new URLSearchParams({
        "grant_type": "",
        "username": email,
        "password": password,
        "client_id": "",
        "client_secret": ""
    }).toString());
    XHR.send(new URLSearchParams({
        "grant_type": "",
        "username": email,
        "password": password,
        "client_id": "",
        "client_secret": ""
    }).toString());
    
    XHR.onreadystatechange = function(){
        if(this.readyState == 4 && this.status == 200){ // 200 is the status code for "OK"
            // The user was successfully logged in
            // Store the access token in local storage
            localStorage.setItem("access_token", this.responseText["access_token"]);
            console.log(this.responseText["access_token"]);
            // Show the user a success message
            Swal.fire({
                title: "Success!",
                text: "Logged in successfully.",
                icon: "success",
                confirmButtonText: "Continue"
            }).then(function(){
                // Redirect the user to the home page
                window.location.href = "index.html";
            });
        } else {
            // The user was not logged in
            // Send error message to the user
            Swal.fire({
                title: "Error!",
                text: "There was an error logging you in."+this.responseText,
                icon: "error",
                confirmButtonText: "Continue"
            }).then(function(){
                // Refresh the login page
                window.location.href = "login.html";
            });
        }
    }
};