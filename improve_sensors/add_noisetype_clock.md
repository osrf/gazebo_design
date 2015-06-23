# Improved sensors and noise modelling in Gazebo
***Gazebo Design Document***

## Overview 

There is a well adopted model for clock error, which is used to account for drift
between the satellite vehicle clocks in the GPS system. 

  dt = a0 + a1 (t - t0) + a2 (t - t0)^2 + k

The a0 term is called the bias, while a1 is the drift. The a2 term is the rate
of drift of the clock with respect to a reference time base. The time t0 is a
reference epoch, and t is the current reference time. k is random noise.

## Requirements ##

## Architecture ##

## Tests ##

## Pull requests ##

None yet