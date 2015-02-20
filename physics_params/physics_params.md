## Project: API for generic physics parameters
***Gazebo Design Document***

### Overview

Each of gazebo's physics engines has many parameters for setting
physical properties of models (e.g. inertia, surface stiffness, joint damping)
and numerical properties of solvers (e.g. iterations, tolerance).
Traditionally, we have manually added physics parameters
to the Gazebo API in the form of Get/Set functions in the physics class,
fields in protobuf messages, and elements in the sdformat description.
This is not a scalable approach, as it would require unreasonable
effort to add all parameters to the API.
Additionally any changes to protobuf messages break ABI,
and thus can only be done on new major versions.

The goal of this design is to specify an interface for getting
and setting physics parameters in a scalable manner without
breaking API/ABI when parameters are added or removed.

### Requirements

Provide mechanisms for reading and writing parameters through

* the Gazebo C++ API
* protobuf messages
* sdformat description files.

Allow parameters to have a variety of types
(similar to boost::any or templates)

* scalar floating point, integer
* vector/matrix floating point, integer
* Pose
* string
* bool

Define conventions for documenting the names, types,
meaning, and units of parameters.

### Architecture

This proposal doesn't contain significant architecture changes,
but rather, mainly interface changes.

### Interfaces

The primary data structure for storing parameters will
be a new protobuf message with a string field for
the name of a parameter and optional fields of
various types corresponding to the parameter value.

~~~
message NamedParameter
{
  required string  name    = 1;
  optional double  Double  = 2;
  optional float   Float   = 3;
  optional string  String  = 4;
  optional vector3 Vector3 = 5;
... etc.
}
~~~

Any gazebo class could offer parameter set and get functions:
~~~
bool GetParam(msgs::NamedPtr &_msg);
bool SetParam(const msgs::NamedPtr &_msg);
~~~

### Performance Considerations

If there are large numbers of parameters, it may require
many string comparisons.
The performance of these interfaces should be profiled.

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
