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
the name of a parameter and optional data fields of
various types corresponding to the parameter value.

~~~
message Param
{
  required string   name           = 1;
  optional Any      value          = 2;
  repeated Param    children       = 3;
}

message Any
{
  optional double  double_value = 1;
  optional int     int_value    = 2;
  optional string  string_value = 3;
  optional Vector3 vector3      = 4;
  optional bool    bool_value   = 5;
}
~~~

The Gazebo side of the implementation must enforce several 
Only one data field of the Any message can be filled at a time.

The `param` message can also be nested. 

The existing `physics` protobuf message will be changed to contain a variable
number of Params:

~~~
import "param.proto"

message Physics
{
  optional Type  type             = 1[default=ODE];
  option double  real_time_factor = 2;
  ...
  repeated Param parameters       = 16;
}
~~~

#### Migration to future Protobuf versions
Map message types are supported in Protobuf 2.6. A map would be the idea way of
implementing the "children" field of the Param message type. The highest Protobuf
that is packaged with Ubuntu Trusty is 2.5.0, so maps would likely not be
integratable until Gazebo 7, which does not support Trusty. Protobuf 2.6 also
supports the "oneof" construct, which would simplify 

Protobuf 3 will introduce Any types, which eliminate the need for the union structure
described above in the structure of `Param`.

Once Protobuf 3 is released and integrated with Gazebo, Param should be changed
to:

```
message Param
{
  required string name        = 1;
  optional Any value          = 2;
  map<string, Param> children = 3;
}
```

#### SDF
A new `param` SDF element keeps consistency between the Protobuf messages,
Gazebo runtime state, and SDF.

The `param` element contains two attributes: `name` and `type`.
Its role is to store a generic key-value pair, where `name` is the key.
Because SDF does not allow variably-typed elements, we also store the type of
the parameter and cast it to the correct type during runtime. `param` values
are stored as `string`.

```
<sdf>
  <world>
    <physics type="ode">
      <ode>
        <param name="extra_friction_iterations" type="double">10</param>
        ...
      </ode>
    </physics>
    ...
  </world>
</sdf>
```

`param` could also be a child/descendant of model, joint, or link.

#### API
New conversion functions will be added for switching between SDF and Protobuf
representations of a Param, adding a primitive as a Param to a Physics message, and
converting a primitive to a Param Protobuf message:

```
template<typename T> msgs::Param ConvertParamSDF(const sdf::ElementPtr _elem);
template<typename T> sdf::ElementPtr ConvertParamSDF(const msgs::Param &_msg);
template<typename T> msgs::Param ConvertParam(const std::String &_key,
    const T &_value);
template<typename T> bool ConvertParam(const msgs::Param &_msg, T _value);
template<typename T> bool AddToPhysicsMsg(const std::string &_key,
    const T &_value, msgs::Physics &_physics);
template<typename T> bool PhysicsMsgParam(const msgs::Physics &_physics,
    const std::string &_key, T &_value);
```

The new Param message could also replace `boost::any` to accomplish the generic
typing used in the Physics library. Any gazebo class could offer parameter set
and get functions:

~~~
bool GetParam(msgs::Param &_msg);
bool SetParam(const msgs::Param &_msg);
~~~

These functions would be accompanied by templated set/get functions that call the
convenience conversion functions:

~~~
template<typename T> bool GetParam(const std::string &_key, T &_value);
template<typename T> bool SetParam(const std::string &_key, const T &_value);
~~~

### Architecture
The new protobuf structure will allow for several architectural changes to the physics
library.

`boost::any` is currently used to for generic type handling in the physics library.
The `Param` protobuf message could replace `boost::any` to simplify the code and
migrate away from reliance on Boost. To settle this design choice, the relative performance
of protobuf messages vs. boost::any could be profiled in
order to determine which has superior speed.

With a mechanism finally in place to keep the physics parameters enumerated in SDF
consistent with the parameters in protobuf, the physics Protobuf message can be used
as the primary storage data structure for physics engines. This will increase performance,
since Protobuf is a more efficient storage mechanism.

### Use Case
Suppose Alice wants to expose a new Bullet parameter, `shrink_factor`,
and use it in a Gazebo world. Previously, she would have to complete several steps before the
change would be propagated to the stable Gazebo release:

1. Submit an SDF pull request to make new element `shrink_factor`,
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
  optional shrink_factor = 42;
}
```

```
bool BulletPhysics::GetParam(std::string key, boost::any value)
{
  ... else if (_key == "shrink_factor")
  {
    value = bulletShrinkFactor;
    return true;
  }
  ...
}
```

```
<sdf>
  <world name="oscars">
    <physics type="bullet">
      <bullet>
        <shrink_factor>1</shrink_factor>
      </bullet>
    </physics>
  </world>
</sdf>
```

With the changes proposed in ther document, Alice only needs to do two things,
and neither break API/ABI in Gazebo. She does not need to change SDF.

1. Add update logic to `BulletPhysics::[G/S]etParam` for the new key.
2. Update world to include new parameter.

```
bool BulletPhysics::GetParam(std::string key, boost::any value)
{
  ... else if (_key == "shrink_factor")
  {
    value = bulletShrinkFactor;
    return true;
  }
  ...
}
```

```
<sdf>
  <world name="oscars">
    <physics type="bullet">
      <bullet>
        <param name="shrink_factor" type="int">1</param>
      </bullet>
    </physics>
  </world>
</sdf>
```

Alice can still submit major pull requests Gazebo and SDF if she
wants to make her new parameter a first-class citizen,
but she doesn't have to.
This saves a lot of time and effort expended in pull request review. It reduces
the number of API/ABI changes made to the code since Protobuf messages do not
need to be changed, which makes the release process smoother.

### Performance Considerations/Questions

If there are large numbers of parameters, it may require
many string comparisons.
The performance of these interfaces should be profiled.

Internally, physics engines could reference parameters by enumeration types.
 (See ODEPhysics::ODEParam for an example of enumerations.) An optimization
could be made by creating a map of <ParamEnum, value> pairs and accessing the
parameters in the map, rather than iterating through a list of enums, which is
marginally better because map access keyed on integers is logarithmic, not linear.

An optional Type field could be added to optimize accessing the `Param` message.

Storing SDF `param` elements as `string` might be wasteful, is there a leaner implementation?

### Tests

1. SDF: Test parsing the `<param>` element.
1. Gazebo: Parameterized tests for physics engine parsing of `physics` protobuf
messages with `params` structure.

### Pull Requests
1. SDF: New `param.sdf` element.
2. Gazebo: Add `param.proto` protobuf message. Add `Params` to `physics.proto`.
Add conversion functions and integrate physics engines with new message structure.
3. Gazebo: Add support for parsing `param.sdf` element with tests for each physics engine.
4. Gazebo: Replace `sdf` storage element in physics engines with `physics` protobuf structure.
5. Gazebo: Replace `boost::any` abstraction with type-variable `param` protobuf structure.
