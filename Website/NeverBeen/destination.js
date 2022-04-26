
const NeverBeenAPI = "http://134.53.116.212:8000";

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
const place = getParameter(placeId);

function onload() {
  getData();
}
// Function that populates all information for destination page
const getData = () => {
    const request = new XMLHttpRequest();
    request.open("get",NeverBeenAPI + "/place/guest/" + place);

    request.onload = function() {
      const data = JSON.parse(request.response);
      console.log(data);
    };

    request.send();
    
};

// Simple Alt getUrlParameter
function getParameter(parameterName){
  let parameters = new URLSearchParams( window.location.search )
  return parameters.get(parameterName);
}


// Create a function "getUrlParameter" that takes in a parameter name and returns the value of the parameter
// This function is used to get the desired parameter from the URL
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}
