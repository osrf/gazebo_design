## Project: TITLE
***Gazebo Design Document***

### Overview

#### Need (Motivation) ####
with the following feedback from Steffi's PAL robotics interview,

    ...The simulation was unstable, joint controllers had to be tuned, friction and contact parameters of the feet should be tuned to avoid the robot started sliding on the ground. The solver or physics engine sometimes gets crazy and the robot explodes (this still happens).

Above is definitely a frequently encountered pattern (similar feedbacks from working with different robot implementers: proxi, ubr1, etc.)

The goal of this project is to identifying and eliminating ***bad/exploding physics solutions*** as a suspect to unstable robot behavio.

#### Approach ####
One solution to addressing the above issue is by providing run-time diagnostics data from active physics engine.

The purpose of physics diagnostics is to help the users determine if the ***bad/unstable behavior*** comes from bad physics solutions or from the user specified model+controller.

#### Benefits ####
Doing so reduces our support role in making simulation user friendly, encourages gazebo adoption.
And we know that typical robot app developers / researchers hates fighting physics engines :). Better to keep them focused on more exciting and meaningful work even if it's modeling related (e.g. tuning model parameters such as joint damping, limit stiffness, contact stiffness, etc or controller gains).


Tooling for identify bad physics solutions: we need a way of visualizing "quality of physics solutions".

Console dump of diagnostics using `gz physics --wtf` or better yet, visualization through `gzclient` GUI.

Physics diagnostics through command line is easier to do (`gz physics --wtf`), but ultimately some form of visualization will be more user friendly.

A little bit about the quality metric that we need to visualize:

 - global RMS constraint error
 - integration discretization error
 - constraint error for each constraint
 - energy content for each link, should be conserved if unactuated.
 - energy content for all links in the world
 - energy added by actuators (bonus if we can visualize energy *removed* by dampers, contacts and friction).

#### Future Benefits ####

Physics diagnostics can be used to construct auto-performance tuning algorithms.


### Requirements

List the set of requirements that this project must fulfill.
If the list gets too long, consider splitting the project into multiple small projects.

For example:

1. GUI should plot values over time, where values can be joint angles, poses of objects, forces on objects, diagnostic signals, and values from topics.
1. Up to four values per plot is allowed.
1. Multiple plots should be supported.

### Architecture
Include a system architecture diagram.
This should be a conceptual diagram that describes what components of Gazebo will be utilized or changed, the flow of information, new classes, etc.

### Interfaces
Describe any new interfaces or modifications to interfaces, where interfaces are protobuf messages, function API changes, SDF changes, and GUI changes. These changes can be notional.

For example:
Plot proto message: A message that carries plot data will be created to transmit data from the server to the client.

Include any UX design drawings.

### Performance Considerations
Will this project cause changes to performance?
If so, describe how.
One or more performance tests may be required.

### Tests
List and describe the tests that will be created. For example:

1. Test: Plot View
    1. case: Plot window should appear when signaled by QT.
    1. case: Plot simulation time should produce correct results when save to CSV
    1. case: Signalling a close should close the plotting window.
1. Test: Multiple plots
    1. case: Create two plots with identical data. Saved CSV data from each should be identical

### Pull Requests
List and describe the pull requests that will be created to merge this project.
Consider separating large refactoring operations from additions of new code.
For example, the physics::SurfaceParams class was refactored in
[pull request #891](https://bitbucket.org/osrf/gazebo/pull-request/891/refactor)
so that a new FrictionPyramid class could be added in
[pull request #935](https://bitbucket.org/osrf/gazebo/pull-request/935/create).

Keep in mind that smaller, atomic pull requests are easier to review.
