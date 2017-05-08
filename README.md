# Sensible

**Sens**ible is a multi-sensor multi-target sensor-fusion library geared towards urban traffic applications. It is built on ZeroMQ's Pub-Sub design pattern for flexibility and scalability.

The framework support parallel, real-time processing and filtering of incoming data from different types of sensors, followed by centralized data association and filtering. In the future, in order to support tracking of a large number of vehicles, the centralized tracking component will be refactored into a decentralized implementation that leverages techniques from distributed, high performance computing. 

Sensible is mainly useful for others doing research in sensor fusion for traffic applications; as such, the algorithms for state estimation and data association can easily be swapped out for experimentation purposes. 

This work is being done as a part of a larger project aimed at developing a complete smart traffic intersection controller that handles both autonomous and conventional vehicles: see our project website [here](avian.essie.ufl.edu).

## TODO

* Create node.js app that listens to BSM port and plots tracks on Google Maps viz