
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

// API call when user fills out the sign up form
const NeverBeenAPI = "http://134.53.116.212:8000";
window.addEventListener( "load", function () {
    function sendData() {
        const XHR = new XMLHttpRequest();
        // Collect information from the form object
        const jsonFormData = buildJsonFormData(form);
        // Define what happens on successful data submission
        XHR.addEventListener( "load", function(event) {
            alert( event.target.responseText );
        } );
        // Define what happens in case of error
        XHR.addEventListener( "error", function( event ) {
            alert( 'Oops! Something went wrong.' );
        } );
        // Set up our request
        XHR.open("POST", NeverBeenAPI + "/createUser", true);
        XHR.setRequestHeader("Content-type", "application/json");
        // The data sent is what the user provided in the form
        XHR.send(JSON.stringify({
            "username": jsonFormData["username"],
            "email": jsonFormData["email"],
            "rawPassword": jsonFormData["rawPassword"]
        }));
    }

    // Access the form element...
    const form = document.getElementById( "Signup" );
    // ...and take over its submit event.
    form.addEventListener( "submit", function ( event ) {
        event.preventDefault();

        sendData();
    } );
} );

function buildJsonFormData(form) {
    const jsonFormData = { };
    for(const pair of new FormData(form)) {
        jsonFormData[pair[0]] = pair[1];
    }
    return jsonFormData;
}

// // API call when user submits login form
// var jwt = localStorage.getItem("jwt");
// console.log(jwt);
// if (jwt != null) {
//   window.location.href = './index.html'
// }

// function login() {
//   const username = document.getElementById("email").value;
//   const password = document.getElementById("rawPassword").value;

//   const xhttp = new XMLHttpRequest();
//   xhttp.open("POST", NeverBeenAPI+"/login");
// //   xhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
//   xhttp.send(JSON.stringify({
//     "username": username,
//     "password": password
//   }));
// //   xhttp.onreadystatechange = function () {
// //     if (this.readyState == 4) {
// //       const objects = JSON.parse(this.responseText);
// //       console.log(objects);
// //       if (objects['access_token'] != null) {
// //         localStorage.setItem("jwt", objects['access_token']);
// //         Swal.fire({
// //           text: "You have been successfully signed in!",
// //           icon: 'success',
// //           confirmButtonText: 'OK'
// //         }).then((result) => {
// //           if (result.isConfirmed) {
// //             window.location.href = './index.html';
// //           }
// //         });
// //       } else {
// //         Swal.fire({
// //           text: "error",
// //           icon: 'error',
// //           confirmButtonText: 'OK'
// //         });
// //       }
// //     }
// //   };
//   return false;
// }