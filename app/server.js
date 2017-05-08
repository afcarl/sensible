// init project
var express = require('express');
var app = express();

var port = process.env.PORT || 3000; 

app.get("/", function (request, response) {
  response.sendFile(__dirname + '/views/index.html');  
});

app.post("/bsm", function (request, response) {
  console.log(request);
});

// listen for requests :)
var listener = app.listen(port, function () {
  console.log('Your app is listening on port ' + listener.address().port);
});