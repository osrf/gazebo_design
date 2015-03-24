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

### Interfaces

#### Protobuf
The primary data structure for storing parameters will
be a new protobuf message with a string field for
the name of a parameter and optional fields of
various types corresponding to the parameter value.

~~~
message NamedParam
{
  enum Type {DOUBLE = 1; FLOAT = 2; INT = 3; STRING = 4 ... }

  required string  name    = 1;

  optional double  double_value = 3;
  optional int     int_value    = 5;
  optional string  string_value = 6;
  optional Vector3 vector3      = 7;
... etc.
}
~~~

The existing `physics` protobuf message will be changed to contain a variable
number of NamedParameters:

~~~
import "namedparam.proto"

message Physics
{
  enum Type
  {
    ODE = 1;
    ...
  }

  optional Type type = 1[default=ODE];

  optional repeated NamedParam = 2;
}
~~~

#### SDF
A new `param` SDF element keeps consistency between the Protobuf messages,
Gazebo runtime state, and SDF.

The `param` element contains three attributes: `name`, `type`, and `value`.
Its role is to store a generic key-value pair, where `name` is the key and
`value` is the value.
Because SDF does not allow variably-typed elements, we also store the type of
the parameter and cast it to the correct type during runtime. `param` values
are stored as `string`.

```
<sdf>
  <world>
    <physics type="ode">
      <ode>
        <param name="extra_friction_iterations" type="double" value="10"/>
        ...
      </ode>
    </physics>
    ...
  </world>
</sdf>
```

#### API

Any gazebo class could offer parameter set and get functions:

~~~
bool GetParam(msgs::NamedParam &_msg);
bool SetParam(const msgs::NamedParam &_msg);
~~~

These functions would be accompanied by templated set/get functions that call the
convenience conversion functions:

~~~
template<typename T> bool GetParam(const std::string &_key, T &_value);
template<typename T> bool SetParam(const msgs::NamedParam &_msg, const T &_value);
~~~

### Architecture
The new 


### Example Usage
Suppose Erwin wants to expose a new Bullet parameter, `academy_awards_won`,
and use it in a Gazebo world. Previously, he would have to complete several steps before the
change would be propagated to the stable Gazebo release:

1. Submit an SDF pull request to make new element `academy_awards_won`,
a child of `bullet` (needed to specify parameter in SDF).
2. Add a new field to the `physics.proto` message (needed for client/server communication,
including visualization of physics parameters). Add update logic for message in
transport callbacks, `BulletPhysics::OnPhysicsMsg` and `BulletPhysics::OnRequest`.
3. Add update logic to `BulletPhysics::[G/S]etParam` for the new key.
4. Update world to include new parameter.

```
message Physics
{
  optional Type type = 1;
  optional string solver_type = 2;
  optional double min_step_size = 3;
  ...
  optional academy_awards_won = 42;
}

BulletPhysics::GetParam()
{
  ... else if (_key == "academy_awards_won")
  {
    return bulletAcademyAwardsWon;
  }
  ...
}

<sdf>
  <world name="oscars">
    <physics type="bullet">
      <bullet>
        <academy_awards_won>1</academy_awards_won>
      </bullet>
    </physics>
  </world>
</sdf>
```

With the changes proposed in this document, Erwin only needs to do two things,
and neither one violates backward compatibility of Protobuf messages or SDF:

1. Add update logic to `BulletPhysics::[G/S]etParam` for the new key.
2. Update world to include new parameter.

```
BulletPhysics::GetParam()
{
  ... else if (_key == "academy_awards_won")
  {
    return bulletAcademyAwardsWon;
  }
  ...
}

<sdf>
  <world name="oscars">
    <physics type="bullet">
      <bullet>
        <param name="academy_awards_won" type="int" value="1"/>
      </bullet>
    </physics>
  </world>
</sdf>
```

Erwin can still submit major pull requests Gazebo and SDF if he
wants to make his new parameter a first-class citizen and stop using the `param`
syntax in SDF. In the meantime, we've saved both Erwin and ourselves lots of time,
effort, and pain related to testing, reviewing and packaging new PRs.

### Performance Considerations

If there are large numbers of parameters, it may require
many string comparisons.
The performance of these interfaces should be profiled.

Internally, physics engines could reference parameters by enumeration types.
 (See ODEPhysics::ODEParam for an example of enumerations.) An optimization
could be made by creating a map of <ParamEnum, value> pairs and accessing the
parameters in the map, rather than iterating through a list of enums, which is
marginally better because map access keyed on integers is logarithmic, not linear.

An optional Type field could be added to optimize accessing the `NamedParam` message.

Storing SDF `param` elements as `string` might be wasteful, is there a leaner implementation?

### Tests


### Pull Requests
1. Gazebo: Add `namedparam.proto` protobuf message. Add `NamedParams` to `physics.proto`.
Add conversion functions and integrate physics engines with new message structure.
2. SDF: New `param.sdf` element.
3. Gazebo: Add support for parsing `param.sdf` element with tests for each physics engine.
4. Replace `sdf` storage element in physics engines with `physics` protobuf structure.
5. Replace `boost::any` abstraction with type-variable `namedparam` protobuf structure.
