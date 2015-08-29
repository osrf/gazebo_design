## Project: Graphically Resize Inertia
***Gazebo Design Document***

### Overview

When modeling a robot, one must choose inertial parameter values
for each rigid body (or Link) in the system.
These parameters include the mass, center of mass location,
and the six components of the symmetric 3x3 moment of inertia matrix.
While intuition can often be used to estimate the mass
and location of the center of mass,
it is very difficult to estimate inertia matrix parameters,
which depend on both the mass and size of an object.

For this reason, visualization of the moment of inertia was added to Gazebo in
[pull request 745](https://bitbucket.org/osrf/gazebo/pull-requests/745)
(see also [issue 203](https://bitbucket.org/osrf/gazebo/issues/203)).
The mass `m` and principal moments of inertia `Ixx`, `Iyy`, and `Izz`
are used to compute the dimensions of a box of uniform density
with equivalent moment of inertia.
For example, a box with dimensions `dx`, `dy`, and `dz`
has the following moment of inertia components:

~~~
Ixx = m/12 (dy^2 + dz^2)
Iyy = m/12 (dz^2 + dx^2)
Izz = m/12 (dx^2 + dy^2)
~~~

The equations can be inverted to express the box dimensions
as a function of mass and inertia components:

~~~
dx = sqrt(6/m (Izz + Iyy - Ixx))
dy = sqrt(6/m (Ixx + Izz - Iyy))
dz = sqrt(6/m (Iyy + Ixx - Izz))
~~~

These calculations are currently used to visualize the inertia of an object
as a pink box.

![inertia box of a sphere](inertia_box.png)

While it is useful to visualize the inertia, it would be even more useful
to be able to modify the inertia using interactive markers.
Gazebo currently has the ability to resize simple shapes,
though it does not currently affect the inertia.

### Requirements

1. When resizing a simple shape, scale the inertia values accordingly.

2. Allow the moment of inertia values to be modified by attaching
interactive markers to the inertia visualization
and scaled in a similar manner to the other resize tool.

![resizing a sphere](inertia_sphere.png)

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
