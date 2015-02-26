## Actuator model for physics library
***Gazebo Design Document***

### Overview
Currently, realistic joint movement in Gazebo requires custom plugin code to simulate physical actuating systems. This design document proposes the implementation of actuator models in the physics library, similar to the sensor noise models in the sensor library. To faithfully simulate real motors, Gazebo developers could input known physical parameters to predefined actuator models we will implement, such as electric or gas motor models. Alternatively, developers could create custom actuator models by extending an abstract actuator interface.

### Requirements

Actuators enforce a set of mathematical relationships between the various dynamic properties of the joint, such as position, velocity, acceleration, or force/torque. An actuator is associated with one or more joints; it will have no effect on the world if it is not attached to a joint. Joints may have zero or more actuators. These relationships may be a function of user-specified parameterized properties such as power or max speed. Joints may share actuators.

Users may want to change the actuator state based on externally modelled variables. External variables are properties that Gazebo joints do not keep track of. For example, users may want to simulate how the remaining battery charge of an electric motor affects actuation. Here, charge is an external variable. The actuator model implementation should include a flexible way of incorporating external variables into the actuator model.

Actuators should be non-physics engine specific and rely solely on the abstract `Joint` interface to function.

### Architecture

New abstract `Actuator` class in `physics`

The `Joint` class will have a data structure to store its actuator(s). In `Joint::SetState`, the actuator(s) are accessed and affect whatever relationship is specified in the Actuator implementation.

Problems:

It would be great if the developer could specify actuator properties in SDF, but it's awkward to support reading actuator parameters in SDF if the user can also specify actuators with custom parameters. Perhaps there should be an abstract ActuatorPlugin to manage the generality... hmm...

### Interfaces

### Examples
This section lists some useful actuator models to be implemented. (TODO)

### Tests

### Pull Requests

### Future Work

