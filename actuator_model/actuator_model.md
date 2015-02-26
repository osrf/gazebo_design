## Actuator model for physics library
***Gazebo Design Document***

### Overview
Currently, realistic control of joints in Gazebo requires custom plugin code to implement physical models. This design document proposes the implementation of actuator models in the physics library, similar to the sensor noise models in the sensor library. To faithfully simulate real motors, Gazebo developers could input known physical parameters to predefined actuator models we will implement, such as electric or gas motor models. Alternatively, developers could create custom actuator models by extending an abstract actuator interface.

### Requirements

Actuators enforce a set of mathematical relationships between the various dynamic properties of the joint, such as position, velocity, acceleration, or force/torque. An actuator is associated with one or more joints; it will have no effect on the world if it is not attached to a joint. Joints may have zero or more actuators. These relationships may be a function of user-specified parameterized properties such as power or max speed.

Users may want to change the actuator state based on externally modelled variables, such as battery power. 

### Architecture

### Interfaces

### Examples
This section lists some useful actuator models to be implemented.

### Tests

### Pull Requests

### Future Work

