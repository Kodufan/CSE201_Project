
const NeverBeenAPI = "http://134.53.116.212:8000";

// This code snippet checks for a "token" query in the URL
// If there is a token query, then the user just clicked the "verify your email" link
// they received after creating their account
var url = window.location;
var token = new URLSearchParams(url.search).get('token');
console.log(token);
if(token!=null){
    // This should only be called when someone is verifying their email for the first time
    var xhttp = new XMLHttpRequest();
    xhttp.open("post", NeverBeenAPI+"/verifyAccount");
    XHR.setRequestHeader("Content-type", "application/json");
    // The data sent is what the user provided in the form
    XHR.send(JSON.stringify({
        "token": token
    }));
}
