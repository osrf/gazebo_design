## Actuator model for physics library
***Gazebo Design Document***

### Overview
Currently, realistic control of Gazebo joints requires custom plugin code to implement physical models. This design document proposes the implementation of actuator models in the physics library, similar to the sensor noise models in the sensor library. To faithfully simulate real motors, Gazebo developers could input known physical parameters to predefined actuator models we will implement, such as electric or gas motor models. Alternatively, developers could create custom actuator models by extending an abstract actuator interface.

### Requirements

An actuator is associated with one joint. Joints may have zero or more actuators. Actuators enforce a set of mathematical relationships between the different dynamic properties of the joint, such as position, acceleration, or torque. These relationships may be a function of user-specified parameterized properties such as power or max speed. 

### Architecture

### Interfaces

### Tests

### Pull Requests

### Future Work

