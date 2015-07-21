## Project: Actuation Mechanism Simulation (Transmissions, Actuators and Sensors)
***Gazebo Design Document***

### Overview

Create a simulation abstraction layer to model robot actuation mechanisms.

Note that a breadth-first search gathering real world robot actuation
system examples preceded this proposed implementations
[here](https://docs.google.com/document/d/1h18Sd2qVMJCRqoWC7gsrhyIuhg6CKPKXIBK1jVf43aM).

### Requirements

Traditionally, gazebo robot control has been approached as an exercise to

1. Read joint and sensor states from Gazebo.
1. Custom code that uses simulated sensor data to provide realistic sensor
   data.
1. Custom controller that does something with the incoming sensor data and 
   computes / sends out controller commands.
1. Custom code that parses real world controller commands, translates them
   to simulated joint commands.
1. Apply joint command (torque, position or velocity command) to simulated
   model in Gazebo.

While this process works well in general, it is cumbersome to setup on a
new robot, debug and verify the pipeline is working correctly.
In addition, this approach has a few undesirable characteristics.  I.e.
it is:

- Very difficult to model more complicated transmissions in a systematic way,
- The existing approach leads to numerically explicit transmission modeling.
  Which means the read-process-act loop creates commands that are always
  one simulation time step behind states. As a result, coupled joint actuation
  dynamics is less efficient, realistic and/or less stable numerically.
- To simulate custom actuated robot means creating custom plugins to emulate real
  robot correctly. This requires a lot of development time and esoteric knowledge
  on the hardware (actuators, interfaces, etc.). This proposed tool
  is meant to help speedup development iteration time.

At a high level, we want to simulate the following objects usually grouped
together in a robotic actuation system:

1. Joint sensors (joint position and velocity encoders, limit sensors, etc.)
1. Transmission (motorhead gearbox, geared joints, belt drive transmissions, etc.)
1. Actuator (motors, solenoids, pneumatic actuators, etc.)

While this design will not solve all actuation system modeling problems, it
will enable:

- Extend modeling of basic joint sensors using SDF,
- Modeling of a basic actuation system using SDF,
- Modeling of basic interfaces and synchronization needs and
- The ability to extend current design to more complex systems.

The modeling process then becomes:

1. Create an Actuator object in SDF.
1. Create an Actuator plugin that recreates real motor API and communications (CANBus/TCP/etc.)
1. Create a Joint Sensor object in SDF.
1. Create a Joint Sensor plugin that recreates real sensor API and communications (CANBus/TCP/etc.).
1. Create a Transmission object in SDF.
1. Create a Controller object that has access to Actuator plugin and Joint Sensor plugin.


#### Open Questions

- Motors sometimes introduce new intermediate joints and links, i.e. it adds an intermediate motor core mass that spins independently of motor casing and motor axle.
- Gearboxes can also introduce intermediate joints and links.  A link is connected to an input shaft, another to the output shaft, then there are stuff (gears) in between that spins/moves at different rates than input or output links.


### Synchronization
The question remains, who and how enforces data synchronization.
To answer this, we will examine a synchronous real-time system more closely.

### Architecture
[Proposed System Diagrams](https://docs.google.com/a/osrfoundation.org/presentation/d/1xRMo5UDr6AuzlWIxP5Uwtgn2YNhEK1MiJAI20F8jFUQ/edit?usp=sharing)

### Interfaces
#### Implementations
Class relationships between objects:
- Joint Sensor has access to Joints, Links or Models (to read position, velocity, accelerations, torque, etc.)
- Actuator has access to Joints, Links or Models (to set position, velocity, torque)
- Actuator plugin will have some comms abstraction. We will use either TCP sockets or CANBus as an example.
- Joint Sensor plugin will have some comms abstraction. We will use either TCP sockets or CANBus as an example.
- Custom Controller can read data from Joint Sensor and send data to Actuator using the same set of comms abstraction.
- Transmission has access to Joints, Links, Models, PhysicsEngine (to create / destroy constraints, links or joints as it sees fit).
    - For exmaple, if the motor is a direct drive motor, one way to simulation this is to simply call Joint::SetForce() to simulate torque application.
    - If the motor has a gearbox, we might have to destroy the existing joint and replace it with two joints plus an intermediate link (motor core). Then add a gearbox constraint between the two joints.

### Performance Considerations
This addition will not change performance of simulations that do not utililize the new proposed method of simulation.

### Tests
Here are the tests that will be created:

1. Test: Joint Sensor class
    1. case: create a test that checks encoder output relative to joint state for different fixed ratios.
    1. case: for custom ratios and offsets.
1. Test: Actuator class
    1. case: Test joint torque application given a motor command.
1. Test: Transmission class
    1. case: Test simple joint coupling (multiplier with offsets)
    1. case: Test simple four bar coupling

### Pull Requests
Pull requests to be created.

Keep in mind that smaller, atomic pull requests are easier to review.
