## Project: Bring the IMU sensor inline with the generic noise models
***Gazebo Design Document***

## Overview ##

The IMU sensor currently has its own bespoke noise model, which duplicates a lot
of the functionality provided by the reusable Gaussian noise model. The purpose
of this document is to phase out the bespoke implementation for the generic one.

## Requirements ##

1. The sensor must be updated to use 6 noise models for its axes of measurement
2. The new sensor noise model must be backward-compatible with the old model

## Architecture ##

In order to support one noise stream for all six measurements produced by the
inertil sensor, the SDF for the IMU must be modified in the following way:

```
<element name="angular_velocity" required="0">
  <description>These elements are specific to body-frame angular velocity,
  which is expressed in radians per second</description>
  <element name="x" required="0">
    <description>Angular velocity about the X axis of the sensor</description>
    <include filename="noise.sdf" required="0"/>
  </element>
  <element name="y" required="0">
    <description>Angular velocity about the Y axis of the sensor</description>
    <include filename="noise.sdf" required="0"/>
  </element>
  <element name="z" required="0">
    <description>Angular velocity about the Z axis of the sensor</description>
    <include filename="noise.sdf" required="0"/>
  </element>
</element>

<element name="linear_acceleration" required="0">
  <description>These elements are specific to body-frame linear acceleration,
  which is expressed in meters per second squared</description>
  <element name="x" required="0">
    <description>Linear acceleration about the X axis</description>
    <include filename="noise.sdf" required="0"/>
  </element>
  <element name="y" required="0">
    <description>Linear acceleration about the Y axis</description>
    <include filename="noise.sdf" required="0"/>
  </element>
  <element name="z" required="0">
    <description>Linear acceleration about the Z axis</description>
    <include filename="noise.sdf" required="0"/>
  </element>
</element>
```
One big open question that I have is how to update the sdf covnerter for 
moving 1.4 -> 1.5, given the changes that we have made to the noise params?

## Performance Considerations ##

The run-time complexity of the new Gaussian sensor should be no worse than the
original sensor, but other noise models may further limit performance.

## Tests ##

1. Ensure that a sensor with the old noise SDF format produces a sensor with
   a Gaussian noise models with matching mean, variance and bias.
2. Ensure that a sen with the new noise SDF produces a sensor with the correct
   noise type for each of the measurement streams.

## Pull requests ##

The [pull request](https://bitbucket.org/osrf/sdformat/pull-request/199/updated-imu-sensor-to-support-six-generic) to update the imu sensor SDF: coming soon

The pull request to update the imu sensor to Gazebo: coming soon