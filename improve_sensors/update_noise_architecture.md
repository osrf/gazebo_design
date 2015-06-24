## Project: Improve the generic noise model architecture
***Gazebo Design Document***

## Overview ##

The current noise model architecture in Gazebo assumes that error is independent
of space or time. Many sensors, such as gyroscopes, actually suffer temporally 
dependent random walks. Other sensors, such as altimeters, suffer spatially
dependent random walks through tropospheric pressure gradients.

The objective of this design document is to propose "linking" the base noise
stream class to its base entity (sensor). By so doing we have access to both a
sensor pose and a simulation time from within the noise mode, as it inherits
its core functionality from the Noise class.

## Requirements ##

1. The Noise constructor takes both a noise SDF and pointer to a sensor
2. The class exposes access to simulation time 
3. The class exposes access to the current sensor pose 

## Architecture ##

Currently, noise streams are instantiated in the following way using a factory
class ```NoiseFactory```, passing a SDF block and an optional sensor string (to
distinguish between cameras and other sensors) to the static method:

```
class GAZEBO_VISIBLE NoiseFactory
{
  public: static NoisePtr NewNoiseModel(sdf::ElementPtr _sdf,
      const std::string &_sensorType = "");
};
```

I propose changing this factory method to the following, and potentially marking
the old method as deprecated at of Gazebo 6.0:

```
class GAZEBO_VISIBLE NoiseFactory
{
  public: static NoisePtr NewNoiseModel(sdf::ElementPtr _sdf,
          sensors::SensorPtr _sensor);
};
```

This preserves the ability to determine the sensor category (image, ray, other)
using the Sensor::GetCategory() method. However, it provides the additional
advantage that you now have the full physical system hierarchy available:

  noise -> sensor -> link -> model -> world

What remains to be added -- which will no-doubt be useful beyond just the noise
models -- are some methods in the sensor class to retrieve aspects about the
simulated world. Off the top of my head, I can see how these functions may be
used to simplify the design of the IMU, GPS, Magnetometer and Altimeter sensor 
classes as well as their plugins:

```
/// \class Noise Noise.hh
/// \brief Noise models for sensor output signals.
class GAZEBO_VISIBLE Sensor
{
  ...

  /// \brief Returns the pose of the sensor in the world frame
  /// \return Sensor pose
  public: math::Pose GetWorldPose() const;
  
  /// \brief Returns the sensor-frame linear acceleration
  /// \return Sensor twist
  public: math::Vector3 GetLocalLinearVelocity() const;

  /// \brief Returns the sensor-frame angular velocity
  /// \return Sensor twist
  public: math::Vector3 GetLocalAngularVelocity() const;

  /// \brief Returns the current simulation time
  /// \return Simulation time
  public: common::Time GetSimulationTime() const;

  ...
}
```

If it's not too risky an idea, one could also provide access to the world 
pointer, allowing things like gravity and magnetic vectors to be accessed by
plugins. Although it may be more sensible to mask these with sensor-specific
proxy functions like ```ImuSensor::GetLocalGravityVector()```.


```
  /// \brief Returns a pointer to the World, allowing access to the gravity
  ///  and geomagnetic vectors, as well as simulation time
  /// \return Pointer to the world in which the sensor exists
  public: physics::WorldPtr GetWorldPtr() const;
````


One of the challenges in the architectural design is to ensure that the noise
models are notified -- and deal with -- events such as a simulation time reset 
and a sudden (discontinuous) change in sensor pose. For the first issue it is
probably sensible to implement a pure virtual Noise::Reset() function that 
is automatically called by Gazebo on all noises when simulation time is reset.

```
/// \class Noise Noise.hh
/// \brief Noise models for sensor output signals.
class GAZEBO_VISIBLE Noise
{
  /// \brief Reset the noise model (when a simulation time is reset)
  protected: virtual void Reset() = 0;
}
```

The spatial reset may be slightly trickier to handle, although I expect it to
present less of a problem. Each noise model that may malfunction in cases where
there are large discontinuous sensor positions change (such as when you use the
hand of God in the GUI) should implement their own method of reset.

## Performance Considerations ##

The run-time complexity of the new Gaussian sensor should be no worse than the
original sensor, but other noise models may further limit performance.

## Tests ##

1. Ensure that a sensor with the old noise SDF format produces a sensor with
   a Gaussian noise models with matching mean, variance and bias.
2. Ensure that the new SDF produces a sensor with the correct noise type for 
   each of the measurement streams.

## Pull requests ##

The pull request to update noise class in Gazebo: coming soon