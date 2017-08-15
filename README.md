# Sensible

**Sens**ible is a multi-sensor multi-target sensor-fusion library geared towards urban traffic applications. It is built on ZeroMQ's Pub-Sub design pattern for flexibility and scalability.

The framework supports distributed, real-time processing and filtering of incoming data from different types of sensors, followed by centralized data association and filtering. In the future, in order to support tracking of a large number of vehicles, the centralized tracking component could be re-written for a multi-core implementation that leverages techniques from high-performance computing. 

Sensible is mainly useful for others doing research in sensor fusion for traffic applications; as such, the algorithms for state estimation and data association can easily be swapped out for experimentation purposes. 

This work is being done as a part of a larger project aimed at developing a complete smart traffic intersection controller that handles both autonomous and conventional vehicles: see our project website [here](avian.essie.ufl.edu).

This work is supported by NSF grant [1446813](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1446813&HistoricalAwards=false).

## Supported features

### Sensors

* Cohda Wireless Mk5 DSRC On-Board-Unit (OBU) with messages forwarded via UDP from a Road-side Unit (RSU) 
* Smartmicro Traffic Radar (UMRR-0F Type-29) via serial port

### Track Filters

* Kalman Filter
* Extended Kalman Filter (recommended)
* Particle Filter

### Kinematics models

* Constant velocity (recommended)
* Constant acceleration

### Track-to-track association

* Single-scan (w/ or w/out cross-correlation estimation) global nearest neighbors
* Multi-scan (w/ or w/out cross-correlation estimation) global nearest neighbors

### Track-to-track fusion

* Covariance Intersection 

## TODO

* [ ] Update synchronizer to support linear interpolation 
* [ ] Update synchronizer to quantize incoming data to fuse at synchronized times
* [ ] Vehicle lane estimation
* [ ] Video camera sensor node and thread
* [ ] Radar - handle stuck/ghost tracks
