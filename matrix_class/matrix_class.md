## Project: Matrix class supporting arbitrary sizes
***Gazebo Design Document***

### Overview

Currently Gazebo's math libraries support 3x3 and 4x4 matrices
 (`gazebo::math::Matrix3` and `gazebo::math::Matrix4`).
In order to support
 [Jacobian matrices](https://bitbucket.org/osrf/gazebo/issue/1165/api-for-extracting-generalized-inertia),
 Gazebo should support
 matrices of arbitrary size as well (`gazebo::math::Matrix`).
Vectors of arbitrary length can be handled as well as a special case
 of the matrix class.

Also, many physics engines have their own implementations of matrix and
 vector math.
With regard to the Jacobian matrices in particular,
 [it has been suggested](https://bitbucket.org/osrf/gazebo/issue/1165/api-for-extracting-generalized-inertia),
 that performance may be enhanced by providing operators that multiply
 by the given matrix rather than returning a copy of the matrix.
This idea will be considered while attempting to maintain
 a simple API.

### Requirements

The `Matrix` class should satisfy the following requirements:

* Support both floating point and integer data types.
* Provide the following operators:
  * `+` Addition
  * `-` Subtraction
  * `*` Multiplication
  * `~` Transpose
* Allow optional functions

Now I'm not sure about this. Should the optional functions be in the Jacobian
 level or on the Matrix level?

~~~
template<typename T>
class Matrix
{
  Matrix(unsigned int rows, unsigned int cols);
}
~~~

https://github.com/chrisdembia/simbody/blob/operational-space-ex/Simbody/include/simbody/internal/TaskSpace.h#L77-L122

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