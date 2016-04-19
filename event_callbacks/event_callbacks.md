## Project: Event callbacks
***Gazebo Design Document***

### Overview

This is an attempt to document the existing infrastructure in gazebo
for registering callback functions that can be triggered by events.
It also analyzes the object lifecycle and ownership patterns
to determine if the current pointer types are appropriate.

### Requirements

1. A set of classes that allow functions with arbitrary
input parameters to be registered as callback functions that will
be called when an event is signaled.
These classes should include a mechanism for un-registering callbacks.

2. An set of events relevant to Gazebo's functionality with
callback arguments defined.
It should be possible to define other events as well.

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
