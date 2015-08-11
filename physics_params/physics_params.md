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
  optional double  double_value  = 1;
  optional int     int_value     = 2;
  optional string  string_value  = 3;
  optional Vector3 vector3_value = 4;
  optional Color color_value = 5;
  optional Pose pose_value = 6;
  optional Quaternion quaternion_value = 7;
  optional bool    bool_value   = 5;
}
~~~

The Gazebo side of the implementation must enforce several constraints on the
Param messages:

* Only one data field of the Any message can be filled at a time.

* The `param` message is hierarchical. Each `param` message can contain a list of
`param` children. A `param` should not contain multiple children with the same name.
If multiple children with the same name are found, only the first child
`param` will be used.

Hierarchical parameters are represented within Gazebo with scoped names.
For example, the ODE-specific physics parameter `sor` is a child of the element
`solver`, which is a child of `ode`, which is a child of `physics`. The scoped name
of this parameter is `physics::ode::solver::sor`. This allows elements
of the same name in different namespaces. For example, an identically-named
parameter exists in Bullet, but it would set using the key `physics::bullet::solver::sor`
in Gazebo. The scoped names are determined by the structure of Protobuf messages (which is
determined by SDF); however, the scoped names are *not* used in the Protobuf representation
of the messages.

The existing `physics` protobuf message will be changed to contain a variable
number of `param`s. This field will obey the same constraints described above.

~~~
import "param.proto"

message Physics
{
  optional Type  type              = 1[default=ODE];
  optional double real_time_factor = 2;
  ...
  repeated Param parameters        = 16;
}
~~~

#### Migration to future Protobuf versions
Map message types are supported in Protobuf 2.6. A map is the ideal way of
implementing the "children" field of the Param message type.

Protobuf 2.6 also supports the "oneof" construct, which would simplify enforcing the
union structure of `Any`. Furthermore, Protobuf 3 will introduce Any types, which
eliminates entirely the need for the custom union structure described above in the
structure of `Param`.

However, the highest Protobuf
that is packaged with [Ubuntu Trusty](http://packages.ubuntu.com/trusty/libdevel/libprotobuf-dev)
or [Ubuntu Utopic](http://packages.ubuntu.com/utopic/libdevel/libprotobuf-dev) is 2.5.0.
Protobuf 2.6.1 is not supported until [Ubuntu Vivid](http://packages.ubuntu.com/vivid/libdevel/libprotobuf-dev).
Therefore, it is unlikely that these features will be used to implement the Gazebo `param`
message until Gazebo 8, which will drop support for Utopic (unless we want to package
Gazebo with a custom-packaged or PPA version of Protobuf 2.6 for Trusty and Vivid).

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

template<typename T> bool ConvertParamFromSDF(const sdf::ElementPtr _elem,
    msgs::Param &_msg);
// Call "bool ConvertParamFromSDF", throw an exception if it returns false
template<typename T> msgs::Param ConvertParamFromSDF(const sdf::ElementPtr _elem);

template<typename T> bool ConvertParamToSDF(const msgs::Param &_msg,
    sdf::ElementPtr _elem);
// Call "bool ConvertParamToSDF", throw an exception if it returns false
template<typename T> sdf::ElementPtr ConvertParamToSDF(const msgs::Param &_msg);

template<typename T> bool ConvertParam(const msgs::Param &_msg, T _value);
// Call "bool ConvertParam", throw an exception if it returns false
template<typename T> msgs::Param ConvertParam(const std::String &_key,
    const T &_value);

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
  <world name="wonderland">
    <physics type="bullet">
      <bullet>
        <shrink_factor>1</shrink_factor>
      </bullet>
    </physics>
  </world>
</sdf>
```

With the changes proposed in this document, Alice only needs to do two things,
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
  <world name="wonderland">
    <physics type="bullet">
      <bullet>
        <param name="shrink_factor" type="int">1</param>
      </bullet>
    </physics>
  </world>
</sdf>
```

Alice can still submit major pull requests Gazebo and SDF if she
wants to make her new parameter a first-class citizen. But she does not
need to substantially change the code in order to use the new implicit
parameter in her research.

### Performance Considerations/Questions

If there are large numbers of parameters, it may require
many string comparisons.
The performance of these interfaces should be profiled.

Internally, physics engines could reference parameters by enumeration types.
 (See `ODEPhysics::ODEParam` for an example of enumerations.) An optimization
could be made by creating a map of `<ParamEnum, value>` pairs and accessing the
parameters in the map, rather than iterating through a list of enums, which is
marginally better because map access keyed on integers is logarithmic, not linear.

An optional Type field could be added to optimize accessing the `Param` message.

Storing SDF `param` elements as `string` might be wasteful, is there a leaner implementation?

### Tests

1. SDF: Test parsing the `<param>` element.
1. Gazebo: Parameterized tests for physics engine parsing of `physics` protobuf
messages with `params` structure.

### Pull Requests
The last two items on this list are optional and may require further forethought before implementation.

1. SDF: New `param.sdf` element integrated, with tests.
2. Gazebo: Add `param.proto` protobuf message. Add `Params` to `physics.proto`.
Add conversion functions and tests.
3. Gazebo: Integrate each physics engine with `param` messages, with parameterized tests.
4. Gazebo: Integrate links for each physics engine with `param` messages, with tests.
5. Gazebo: Integrate joints for each physics engine with `param` messages, with tests.
6. Gazebo: Update GUI to reflect custom parameters in the left-hand menu.
7. Gazebo: Replace `sdf` storage element in physics engines with `physics` protobuf structure.
8. Gazebo: Replace `boost::any` abstraction with type-variable `param` protobuf structure.
