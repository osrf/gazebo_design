# Add a magnetometer sensor to Gazebo
***Gazebo Design Document***

## Overview 

A triaxial magnetometer sensor measures the magnetic field strength (in Tesla) 
along three mutually orthogonal axes. It is frequently used to measure the 
Earth's magnetic field, and can be fused with an IMU to estimate orientation.
 
## Requirements

1. The sensor must report the global magnetic field rotated into the body frame
1. The sensor must perturb the three magnetometer axes with unique noise models

## Architecture

SDF already supports the magnetometer sensor, but the implementation needs to be
updated in order to support three independent noise models -- one per axis:

```
<element name="magnetometer" required="0">
  <description>These elements are specific to a Magnetometer sensor.</description>
  <x>
    <include filename="noise.sdf" required="0"/>
  </x>
  <y>
    <include filename="noise.sdf" required="0"/>
  </y>
  <z>
    <include filename="noise.sdf" required="0"/>
  </z>
</element>
```

The implementation of the magnetometer relies on the physics engine providing
the magnetic field in the global frame. Athough there already limited support 
for obtaining a magnetic field vector, an accessor must be added to the
existing ```PhysicsEngine``` class:

```
math::Vector3 PhysicsEngine::GetMagneticField() const
{
  return this->sdf->Get<math::Vector3>("magnetic_field");
}
```

The sensor itself requires a new message definition in Gazebo:

```
package gazebo.msgs;

/// \ingroup gazebo_msgs
/// \interface Magnetometer
/// \brief Data from a magnetic field strength sensor

import "time.proto";
import "vector3d.proto";

message Magnetometer
{
  required Time stamp                = 1;
  required string entity_name        = 2;
  required Vector3d field_tesla      = 3;
}
```

The update implementation for the new ```MagnetometerSensor``` class essentially
just rotates the global magnetic field into body frame coordinates using the
current orientation of the sensor, then perturbs each axis if the body-frame 
measurement with errors drawn from three sensor noise models:

```
bool MagnetometerSensor::UpdateImpl(bool /*_force*/)
{
  // Get latest pose information
  if (this->parentLink)
  {
    // Get pose in gazebo reference frame
    math::Pose magPose = this->pose + this->parentLink->GetWorldPose();

    // Get the reference magnetic field
    math::Vector3 M = this->world->GetPhysicsEngine()->GetMagneticField();

    // Rotate the magnetic field into the body frame
    M = magPose.rot.GetInverse().RotateVector(M);

    // Apply position noise before converting to global frame
    M.x = this->noises[MAGNETOMETER_X_NOISE_TESLA]->Apply(M.x);
    M.y = this->noises[MAGNETOMETER_Y_NOISE_TESLA]->Apply(M.y);
    M.z = this->noises[MAGNETOMETER_Z_NOISE_TESLA]->Apply(M.z);

    // Set the IMU orientation
    msgs::Set(this->magMsg.mutable_field_tesla(),M);
  }

  // Save the time of the measurement
  msgs::Set(this->magMsg.mutable_time(), this->world->GetSimTime());

  // Publish the message if needed
  if (this->magPub)
    this->magPub->Publish(this->magMsg);

  return true;
}
```
These changes will be accompanied by smaller necessary updates to the files:

1. sensors/SensorTypes.hh
2. sensors/CMakeLists.txt
2. msgs/CMakeLists.txt

## Tests ##

1. When aligned with the origin, the sensor should report global magnetic field
2. When rotated PI/2 about the Z axis the sensor should report the magnetic
   field rotated into the body frame.

## Pull requests ##

The pull request to update the magnetometer sensor SDF is here

The pull request to add the magnetometer sensor to Gazebo is here