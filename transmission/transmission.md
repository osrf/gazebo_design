## Project: Actuation Mechanism Simulation (Transmissions, Actuators and Sensors)
***Gazebo Design Document***

### Overview

Create a simulation abstraction layer to model robot actuation mechanisms.

Note that a breadth-first search gathering real world robot actuation
system examples preceded this proposed implementations
[here](https://docs.google.com/document/d/1h18Sd2qVMJCRqoWC7gsrhyIuhg6CKPKXIBK1jVf43aM).

### Requirements

Approach to simulating motors, transmissions and joint sensors can be infinitely
complicated. Therefor it is very important that we scope this proposal precisely.
The goal here is to define minimal set of information needed for a physically
accurate actuator-transmission-encoder model.

A target use case might be:

1. Simulate brushless DC motors with direct drive transmission
   and hall effect sensors as encoders.

Here are some basic scoping statements. We will:

1. For motors:
    1. Simulate idealized torque, torque-speed curve.
    1. Simulate stall torque.
    1. Not simulate electrical properties of the motor (E.g. back EMF, current
       controller, phase commutation torque ripple effects, etc.) here,
       but allow the user to easily extend the model to include electrical effects.
1. For transmission and joint couplings:
    1. Simulate idealized loss-less torque distributions.
    1. Not simulate every single gear component dynamics.
1. For joint sensors (encoders):
    1. Simulate idealized joint position or velocity sensors.
    1. Not simulate common hall effect sensor raw outputs (but allow
       users to do so if they wish).

Traditionally, gazebo robot control has been approached as an exercise to

1. Operate in idealized joint states, assume sensor state can be parsed
   directly from joint state, and motor torque transfers directly to joint torque.
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

So in a way, Actuator, Transmission or Encoder are glorified SDF models,
each can be composed of Joints, Links and convenience function calls to
model members in Gazebo.

#### Open Questions

- Motors sometimes introduce new intermediate joints and links, i.e. it adds an intermediate motor core mass that spins independently of motor casing and motor axle.
- Gearboxes can also introduce intermediate joints and links.  A link is connected to an input shaft, another to the output shaft, then there are stuff (gears) in between that spins/moves at different rates than input or output links.
- How structured are these glorified SDF models for actuators and transmissions? What do we allow users to change? How can we impose structure to these models without reducing flexibility?


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

The Actuator class takes motor commands from custom controller,
and outputs motor control, which is one or more motor command torques.
For direct drive transmission, the motor torque can be applied directly to a joint toruqe.
For more complicated transmission, where there is multi-joint coupling,
the command torque needs to map to several joint torques.
The mapping is to be defined in a Transmission object either by means of
building real physics models (four bar linkage, gearbox, etc.),
or by some fictitious logic that lives in the Transmission class that
determines where and how the command torque should be split up to targeted joint torques.

So to sumarize, an Actuator object can do one of the two things (or both):

1. (Optional) Create a physics coupling mechanism (four bar linkage, gearbox, friction?), then
1. (Required) Specify a motor torque to joint torque mapping.

#### Example SDF

~~~
<model name="test_model">

  <link name="test_link_1">
  </link>

  <link name="test_link_2">
  </link>

  <joint name="test_joint_01" type="revolute">
    <parent>world</parent>
    <child>test_link_1</child>
  </joint>

  <joint name="test_joint_12" type="revolute">
    <parent>test_link_1</parent>
    <child>test_link_2</child>
  </joint>

  <actuator name="test_actuator_01" type="electric_motor">
    <joint>test_joint_01</joint>
  </actuator>

  <actuator name="test_actuator_12" type="electric_motor">
    <joint>test_joint_12</joint>
  </actuator>

  <transmission name="test_generic_transmission" type="linear_map">
    <!--
      Let vector a denote an array of actuator efforts as defined by <actuator_array>,
                   where na is the size of the actuator array.
      Let scalar j denote the array of resulting joint efforts defined by <joint_array>,
                   where nj is the size of the joint array.
      Let vector o_a denote array of actuator effort offsets.
      Let vector o_j denote array of joint effort offsets.
      Let matrix t_aj with dimensions nj X na denote transform from
                      actuator efforts to joint efforts.
                      t_aj defaults to the identity matrix, so if left unspecified,
                      actuator maps to joints one-on-one.

      The conversion from actuator efforts into joint efforts is defined by
      equation below:

        [j] = [t_aj] x ([a]+[o_a]) + [o_j]

      Lastly, the resulting joint effort array j is
      truncated by (joint_effort_lower, joint_effort_upper).
    -->

    <!-- actuator array used for simple linear transmission mapping -->
    <actuator_array>
      test_joint_01
      test_joint_12
    </actuator_array>

    <joint_array>
      test_joint_01
      test_joint_12
    </joint_array>

    <mapping>
      <t_aj>
        1.0 0.0
        0.0 1.0
      </t_aj>
      <actuator_offsets>
        0 0
      </actuator_offsets>
      <joint_offsets>
        0 0
      </joint_offsets>
      <joint_effort_lower>
        0 0
      </joint_effort_lower>
      <joint_effort_upper>
        10 10
      </joint_effort_upper>
    </mapping>
  </transmission>

  <plugin name="custom_transmission_plugin" filename="libCustomTransmissionPlugin.so">
    <!--
      A more generic approach is to let user define a plugin that maps from
      actuator outputs to joint commands using a custom defined function,
      so the mapping can also depends on other simulation states:

        j = F(a, ...)

      The user extends the Transmission class, and implement custom mapping in place
      of the linear_mapping.
    -->

    <actuator_array>
      test_joint_01
      test_joint_12
    </actuator_array>

    <joint_array>
      test_joint_01
      test_joint_12
    </joint_array>
  </plugin>

  <transmission name="test_transmission" type="custom_functions">
    <!--
      Alternative format for the generic approach, where the plugin
      is specific to the transmission class, and contains a conversion
      function that overloads the one in the Transmission class:

        j = F(a, ...)
    -->

    <actuator_array>
      test_joint_01
      test_joint_12
    </actuator_array>

    <joint_array>
      test_joint_01
      test_joint_12
    </joint_array>

    <mapping_plugin name="custom_transmission_plugin" filename="libCustomTransmissionPlugin.so"/>
  </transmission>

  <encoder name="test_encoder" type="position">
    <!-- Sometimes we want to compute position using multiple joints,
         E.g. differential drive, where the encoder output might be
         the position of another transmissioned joint, or numerically
         a weighed mixture of two or more joints.
         Based on this requirement, the encoder should
         connect to a transmission, and not a joint specifically.  -->

    <!-- use this transmission to obtain coupling or mechanical reduction information -->
    <transmission>test_transmission</transmission>
  </encoder>

</model>
~~~

One thought was We can implement everything as plugins for the first pass and determine
later if it is worth the effort to upgrade these to Gazebo classes. But on second thought
that approach requires us to implement a transport mechanism for data flow between
the different proposed objects (i.e. encoders, actuators and transmissions), and
will further complicate things.

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
