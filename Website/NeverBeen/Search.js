 function searchShow(){
 const NeverBeenAPI = "http://134.53.116.212:8000/places/guest?order=Popularity&latitude=0&longitude=0&skip=0&limit=5";
 fetch(NeverBeenAPI)
 .then(response=> response.json())
 .then((jsonData)=>{
   console.log(jsonData);
   const results = jsonData.map(element => element.friendlyName);
   renderResults(results);
 });
 }
//
// let searchTimeoutToken = 0;
//
 function renderResults(results){
   const list = document.getElementById("resultsList");
   list.innerHTML = "";
   results.forEach(result => {
     const element = document.createElement("li");
     element.innerText = result;
     list.appendChild(element);
   });

 }
//
 window.onload = () =>{
   const searchFieldElement = document.getElementById("searchField");
   searchFieldElement.onkeyup = (event) => {
     searchShow(searchFieldElement.value);
   };
 }
