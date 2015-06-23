# Add an altimeter sensor to Gazebo
***Gazebo Design Document***

## Overview 

GPS altitude tends to have a larger error component (at least several meters) in
standard autonomous positioning mode. TFor this reason quadrotors typically use
barometric pressure as an altitude sensor. The output of this sensor is simply
an estimated vertical position (with respect to a reference) and velocity.

## Requirements

1. The sensor must be able to store / periodically update a reference height
1. The sensor must report relative height in meters with repect to the reference
1. The sensor must report absolute vertical velocity in meters per second
1. The sensor must support separate noise streams for the position and velocity

More complicated behaviour, such as the way in which a true barometric sensor
would respond to tropospheric conditions, can be implemented as a plugin.

## Architecture

Implementing the sensor will involve adding the following to SDF:

```
<element name="altimeter" required="0">
  <description>These elements are specific to an altimeter sensor.</description>

  <element name="vertical_position" required="0">
    <description>
      Noise parameters for vertical position
    </description>
    <include filename="noise.sdf" required="0"/>
  </element>

  <element name="vertical_velocity" required="0">
    <description>
      Noise parameters for vertical velocity
    </description>
    <include filename="noise.sdf" required="0"/>
  </element>

</element>
```

To begin with a new message type (altimeter.proto) will need to be created:

```
package gazebo.msgs;

/// \ingroup gazebo_msgs
/// \interface Altimeter
/// \brief Data from an atimeter sensor

import "time.proto";

message Altimeter
{
  required Time time                 = 1;
  required double vertical_position  = 2;
  required double vertical_velocity  = 3;
  required double vertical_reference = 4;
}
```


The implementation (AtimeterSennsor) of the sensor will simply add the pose of
the sensor to the pose of the link to which it is attached, then take the Z 
component of the resulting position and subtract a reference height from it. The
velocity will be calculated directly from the link's world linear velocity:

```
bool AltimeterSensor::UpdateImpl(bool /*_force*/)
{
  // Get latest pose information
  if (this->parentLink)
  {
    // Get pose in gazebo reference frame
    math::Pose altPose = this->pose + this->parentLink->GetWorldPose();
    math::Vector3 altVel = this->parentLink->GetWorldLinearVel(this->pose.pos);

    // Apply noise to the position and velocity 
    this->altMsg.mutable_vertical_position() = 
      this->noises[ALTIMETER_POSITION_NOISE_METERS].Apply(
        altPose.pos.z - this->altMsg.vertical_reference());
    this->altMsg.mutable_vertical_velocity() = 
      this->noises[ALTIMETER_VELOCITY_NOISE_METERS_PER_S].Apply(altVel.z);
  }

  // Save the time of the measurement
  msgs::Set(this->altMsg.mutable_time(), this->world->GetSimTime());

  // Publish the message if needed
  if (this->altPub)
    this->altPub->Publish(this->altMsg);

  return true;
}
```

The sensor will also have the following function for plugin access:

```
/// \brief Accessor for current vertical position
/// \return Current vertical position
public: double GetVerticalPosition();

/// \brief Accessor for current vertical velocity
/// \return Current vertical velocity
public: double GetVerticalVelocity();

/// \brief Accessor for the reference altitude
/// \return Current reference altitude
public: double GetReferenceAltitude();

/// \brief Accessor for current vertical velocity
/// \param[in] _refAlt reference altitude
public: void SetReferenceAltitude(double _refAlt);
```

These changes will be accompanied by smaller necessary updates to the files:

1. sensors/SensorTypes.hh
2. sensors/CMakeLists.txt
2. msgs/CMakeLists.txt

## Tests ##

1. A sensor placed at (0,0,0) should report a vertical position/velocity of zero
1. A sensor placed at (0,0,10) should report a vertical position of 10

## Pull requests ##

The pull request to add the atimeter sensor SDF is here

The pull request to add the altimeter sensor to Gazebo is here