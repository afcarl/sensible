  var config = {
    apiKey: "AIzaSyDxj0dVbEApXX5iXMAZTnkIDd7WaZaZwek",
    authDomain: "sensible-viz-1494193988644.firebaseapp.com",
    databaseURL: "https://sensible-viz-1494193988644.firebaseio.com",
  };

  firebase.initializeApp(config);
  var rootRef = firebase.database().ref();

  function makeInfoBox(controlDiv, map) {
    // Set CSS for the control border.
    var controlUI = document.createElement('div');
    controlUI.style.boxShadow = 'rgba(0, 0, 0, 0.298039) 0px 1px 4px -1px';
    controlUI.style.backgroundColor = '#fff';
    controlUI.style.border = '2px solid #fff';
    controlUI.style.borderRadius = '2px';
    controlUI.style.marginBottom = '22px';
    controlUI.style.marginTop = '10px';
    controlUI.style.textAlign = 'center';
    controlDiv.appendChild(controlUI);

    // Set CSS for the control interior.
    var controlText = document.createElement('div');
    controlText.style.color = 'rgb(25,25,25)';
    controlText.style.fontFamily = 'Roboto,Arial,sans-serif';
    controlText.style.fontSize = '100%';
    controlText.style.padding = '6px';
    controlText.innerText = 'This map shows all active tracks and trajectories.';
    controlUI.appendChild(controlText);
  }

  function initAuthentication(email, password, onAuthSuccess) {
    firebase.auth().signInWithEmailAndPassword(email, password).catch(function(error) {
        console.log('Login Failed!', error);
    });
    firebase.auth().onAuthStateChanged(function(user) {
        if (user) {
          onAuthSuccess();
        }
    });
  }

  var activePoints = [];

  function initMap() {
    var map = new google.maps.Map(document.getElementById('map'), {
      center: {lat: 29.6216931, lng: -82.3867591},
      zoom: 16,
      mapTypeId: google.maps.MapTypeId.SATELLITE,
    });
    // Create the DIV to hold the control and call the makeInfoBox() constructor
    // passing in this DIV.
    var infoBoxDiv = document.createElement('div');
    var infoBox = new makeInfoBox(infoBoxDiv, map);
    infoBoxDiv.index = 1;
    map.controls[google.maps.ControlPosition.TOP_CENTER].push(infoBoxDiv);

    initAuthentication('pemami@ufl.edu', 'password', function() {
      var tracks = rootRef.child('/track');

      tracks.on("child_added", function(child) {
        var newPoint = child.val();
        // remove all currently active points for this track
        for (var i = 0; i < activePoints.length; i++) {
          if (newPoint.track_id === activePoints[i]['id'] && (!(newPoint.sensor === "DSRC" && activePoints[i]['sensor'] === "Fused"))) {
            c = activePoints.pop(activePoints[i]);
            c['point'].setMap(null);
            c['point'] = null;
          }
        }

        if (newPoint.state === "ZOMBIE") {
            return;
        }

        var color = '#FFFFFF'; // white
        if (newPoint.sensor === "Radar") {
          color = '#0033FF'; // blue
        }
        else if (newPoint.sensor === "DSRC") {
          color = '#FF0000'; // red
        }
        else if (newPoint.sensor === "Fused") {
          color = '#FFFF00'; // yellow
        }

        var opaque = 1.0; // change based on state
        if (newPoint.state === "UNKNOWN" || newPoint.state === "ZOMBIE") {
            opaque = 0.35
        } else if (newPoint.state === "CONFIRMED") {
            opaque = 0.9
        } else if (newPoint.state === "DEAD") {
            opaque = 0.1
        }

        /*
        var labelText = newPoint.track_id
        var myOptions = {
          content: labelText,
          boxStyle: {
            border: "none",
            textAlign: "center",
            fontSize: "10pt",
            width: "50px"
          },
          disableAutoPan: true,
          pixelOffset: new google.maps.Size(-25, -5),
          position: google.maps.LatLng(newPoint.lat, newPoint.lon),
          closeBoxURL: "",
          isHidden: false,
          pane: "floatPane",
          enableEventPropagation: true
        };

        var ibLabel = new InfoBox(myOptions);
        ibLabel.open(map);
        */
        var circ = new google.maps.Circle({
          strokeColor: color,
          strokeOpacity: opaque,
          strokeWeight: 1,
          fillColor: color,
          fillOpacity: opaque,
          map: map,
          center: {lat: parseFloat(newPoint.lat), lng: parseFloat(newPoint.lon)},
          radius: 1.5
        });

        activePoints.push({id: newPoint.track_id, point: circ, sensor: newPoint.sensor});
      });
    });
  }