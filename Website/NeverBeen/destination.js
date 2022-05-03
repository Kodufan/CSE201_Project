
const NeverBeenAPI = "http://134.53.116.212:8000";

function onload() {
  dataPopulate();
}

/*------------Attributes-----------------
Place:
  "plusCode": "string",
  "friendlyName": "string",
  "country": "string",
  "description": "string",
  "placeID": 0,
  "posterID": "string",
  "rating": 0,
  "thumbnails": [
    {
      "imageID": 0,
      "uploader": "string",
      "placeID": 0,
      "externalURL": "string",
      "uploadDate": "2022-04-11T21:04:45.542Z"
    }
"comments": [
    {
      "placeID": 0,
      "ratingValue": 0,
      "commentBody": "string",
      "ratingID": 0,
      "username": "string",
      "timePosted": "2022-04-11T21:04:45.542Z",
      "timeEdited": "2022-04-11T21:04:45.542Z"
    }
  ]
*/

// Function that populates reqursts from api
function dataPopulate() {
    const request = new XMLHttpRequest();
    request.open("get",NeverBeenAPI + "/place/guest/" + getUrlParameter("placeId"));

    request.onload = function() {
      const data = JSON.parse(request.response);
      console.log(data);
      document.getElementById("title").innerHTML = data['friendlyName'];
      document.getElementById("country").innerHTML = data['country'];
      document.getElementById("desc").innerHTML = data['description'];
      document.getElementById("rate").innerHTML = "Rating: " + data['rating'];
      document.getElementById("pic").src = data['thumbnails']['0']['externalURL'];
      document.getElementById("comments").innerHTML =  
      data['comments']['0']['ratingValue'] + " star rating   |   comment: " + 
      data['comments']['0']['commentBody'] + "\r ( commented by " +
      data['comments']['0']['username'] + " )";
    };

    request.send();
};


// Create a function "getUrlParameter" that takes in a parameter name and returns the value of the parameter
// This function is used to get the desired parameter from the URL
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}
