// init project
var express = require('express');
var app = express();
var qs = require('querystring');
var firebase = require('firebase');
var port = process.env.PORT || 3000; 

app.use(express.static('public'));

// initialize firebase
var config = {
  apiKey: "AIzaSyDxj0dVbEApXX5iXMAZTnkIDd7WaZaZwek",
  authDomain: "sensible-viz-1494193988644.firebaseapp.com",
  databaseURL: "https://sensible-viz-1494193988644.firebaseio.com",
};

firebase.initializeApp(config);

var track = {
    sender: null,
    track_id: null,
    lat: null,
    lon: null,
    state: null,
    sensor: null,
    zombie_count: null
}

function addToFirebase(track) {
    var ref = firebase.database().ref('/track').push(track, function(err) {
        if (err) {
            console.warn(err);
        }
    });
}

function initAuthentication(email, password) {
  firebase.auth().signInWithEmailAndPassword(email, password).catch(function(error) {
      console.log('Login Failed!', error);
  });
  firebase.auth().onAuthStateChanged(function(user) {
      if (user) {
        track.sender = user.uid;
      }
  });
};

app.get("/", function (request, response) {
    response.sendFile(__dirname + '/views/index.html');
    // Create an anonymous user for this session
    initAuthentication('pemami@ufl.edu', 'password');
});

app.post("/track", function (request, response) {
    var body = '';
    request.on('data', function (data) {
        body += data;

        // Too much POST data, kill the connection!
        // 1e6 === 1 * Math.pow(10, 6) === 1 * 1000000 ~~~ 1MB
        if (body.length > 1e6)
            request.connection.destroy();
    });

    request.on('end', function () {
        var post = qs.parse(body);
        track.track_id = post['track_id'];
        track.lat = post['lat'];
        track.lon = post['lon'];
        track.sensor = post['sensor'];
        track.state = post['state']
        track.zombie_count = post['zombie_count']
        addToFirebase(track)
    });

    response.status(200).end();
});

// delete all tracks in db for a given track_id
app.post("/delete", function (request, response) {
    var body = '';
    request.on('data', function (data) {
        body += data;

        // Too much POST data, kill the connection!
        // 1e6 === 1 * Math.pow(10, 6) === 1 * 1000000 ~~~ 1MB
        if (body.length > 1e6)
            request.connection.destroy();
    });

    request.on('end', function () {
        var post = qs.parse(body);
        var ref = firebase.database().ref('/track')
        ref.orderByChild('track_id').equalTo(post['track_id']).once("value", function(snapshot) {
            var updates = {}
            snapshot.forEach(function(child) {
                updates[child.key] = null;
            });
            ref.update(updates);
        });
    });

    response.status(200).end();
});

// listen for requests :)
var listener = app.listen(port, function () {
  console.log('Your app is listening on port ' + listener.address().port);
});