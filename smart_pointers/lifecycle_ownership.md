# Object lifecycle and ownership in Gazebo
***Gazebo Design Document***

## Overview

Gazebo currently has some problems using shared pointers
with reference loops that prevent proper object destruction.
The broader issue, however, is that we haven't made a coherent
plan for the intended lifecycle of the components in a Gazebo
simulation, where lifecycle means the timing of when objects
are created and destroyed.
Once the lifecycle is known, object ownership can be determined,
which refers to which objects are allowed to create and delete
other objects.
Only after the lifecycle and ownership patterns are defined
should the pointer type be chosen.

For a simple example, consider a class `Foo` with a private
implementation (PIMPL) class `FooPrivate`.

* Lifecycle: Each `Foo` object should have a `FooPrivate` object upon creation
and keep it until the parent `Foo` is destroyed.
* Ownership: Since the `FooPrivate` object must be destroyed with its parent,
the parent is a unique owner.
* Implementation: The PIMPL idiom is used so that the parent class can be
agnostic of the details of `FooPrivate` for ABI compatibility.
As such, `Foo` should forward declare `FooPrivate` and store a private pointer
to a `FooPrivate` object.
Since the `Foo` object is a unique owner, `std::unique_ptr` is an
appropriate choice.

Now consider a more complex example that is based on gazebo physics
classes but with many missing components.
A class `World` contains multiple `Model` objects.

* Lifecycle: After a `World` object has been created, `Model` objects
can be attached to a single world (not shared between worlds).
The models can be deleted at any time.
Any models still existing when the world is being deleted
will be deleted as well.
* Ownership: The `World` object is certainly an owner of the `Model` objects,
but is it a unique owner?
Since the models can be deleted at any time,
care should be taken if other resources intend to use the models.
One approach to resolving the possibility of imminent model destruction
is to share ownership, though that risks the models not being deleted
when the world itself is deleted.
* Implementation: Given the uncertainty about ownership, it is
unclear what pointer types should be used by the `World` to
reference the `Model` objects.
We do know that the models must not outlive the world,
so the `Model` objects should be able to use a raw `World*` pointer.

This document will attempt to describe Gazebo's architecture and propose
appropriate lifecycle and ownership patterns for each component.

## Global and static class variables

The first set of variables to consider is the global and static class
variables used in the component gazebo libraries.
These variables remain in scope for the duration of the program.
A list of global variables can be extracted from ELF files using the `nm` tool.
For example, consider the gazebo math library:

### gazebo_math library

~~~
$ nm -C gazebo/math/libgazebo_math.so | grep ' [BRu] '
000000000023b710 B __bss_start
000000000023baa8 B _end
000000000023b980 B gazebo::math::Pose::Zero
000000000023b9d0 B gazebo::math::Rand::randGenerator
000000000023b9d8 B gazebo::math::Rand::seed
000000000023b750 B gazebo::math::Angle::Pi
000000000023b760 B gazebo::math::Angle::Zero
000000000023b730 B gazebo::math::Angle::TwoPi
000000000023b740 B gazebo::math::Angle::HalfPi
000000000023b780 B gazebo::math::Matrix3::ZERO
000000000023b7e0 B gazebo::math::Matrix3::IDENTITY
000000000023b840 B gazebo::math::Matrix4::ZERO
000000000023b8e0 B gazebo::math::Matrix4::IDENTITY
000000000023ba60 B gazebo::math::Vector3::One
000000000023ba80 B gazebo::math::Vector3::Zero
000000000023ba40 B gazebo::math::Vector3::UnitX
000000000023ba20 B gazebo::math::Vector3::UnitY
000000000023ba00 B gazebo::math::Vector3::UnitZ
~~~

This lists the names of the symbols, which can then be cross-referenced
with the class definitions to determine type.
All but the following variables are `const`:

~~~
Rand.cc:93:      private: static GeneratorType *randGenerator;
Rand.cc:95:      private: static uint32_t seed;
~~~

The `seed` variable is an integer, so it will be cleaned up automatically.
The `randGenerator` variable is a pointer, so it will not be cleaned up
(see [ign-math issue 44](https://bitbucket.org/ignitionrobotics/ign-math/issues/44)
to discuss a fix for this).

### gazebo_common library

The gazebo common library has more of these variables:

~~~
$ nm -C -l gazebo/common/libgazebo_common.so | grep ' [BRu] '
00000000002d1da0 B __bss_start
00000000002d2fd0 B _end
00000000002d2190 u guard variable for SingletonT<gazebo::common::SystemPaths>::GetInstance()::t
00000000002d2dc0 u guard variable for SingletonT<gazebo::common::ModelDatabase>::GetInstance()::t
00000000002d2820 B gazebo::event::Events::postRender
00000000002d28a0 B gazebo::event::Events::worldReset
00000000002d27a0 B gazebo::event::Events::createSensor
00000000002d2920 B gazebo::event::Events::deleteEntity
00000000002d27c0 B gazebo::event::Events::removeSensor
00000000002d29a0 B gazebo::event::Events::worldCreated
00000000002d27e0 B gazebo::event::Events::diagTimerStop
00000000002d2980 B gazebo::event::Events::entityCreated
00000000002d2800 B gazebo::event::Events::diagTimerStart
00000000002d28c0 B gazebo::event::Events::worldUpdateEnd
00000000002d2900 B gazebo::event::Events::worldUpdateBegin
00000000002d2960 B gazebo::event::Events::setSelectedEntity
00000000002d28e0 B gazebo::event::Events::beforePhysicsUpdate
00000000002d2a00 B gazebo::event::Events::step
00000000002d29e0 B gazebo::event::Events::stop
00000000002d2a20 B gazebo::event::Events::pause
00000000002d2840 B gazebo::event::Events::render
00000000002d29c0 B gazebo::event::Events::sigInt
00000000002d2940 B gazebo::event::Events::addEntity
00000000002d2860 B gazebo::event::Events::preRender
00000000002d2880 B gazebo::event::Events::timeReset
00000000002d2d80 B gazebo::common::ModelDatabase::myself
00000000002d2ca0 B gazebo::common::MaterialDensity::materials
00000000002d2f10 B gazebo::common::Time::wallTimeISO
00000000002d2f00 B gazebo::common::Time::clockResolution
00000000002d2ed0 B gazebo::common::Time::Hour
00000000002d2ef0 B gazebo::common::Time::Zero
00000000000ad284 R gazebo::common::Time::nsInMs
00000000002d2ee0 B gazebo::common::Time::Second
00000000000ad288 R gazebo::common::Time::nsInSec
00000000002d2f20 B gazebo::common::Time::wallTime
00000000002d2060 B gazebo::common::Color::Red
00000000002d2020 B gazebo::common::Color::Blue
00000000002d2080 B gazebo::common::Color::Black
00000000002d2040 B gazebo::common::Color::Green
00000000002d20a0 B gazebo::common::Color::White
00000000002d2000 B gazebo::common::Color::Yellow
00000000002d2a80 B gazebo::common::Image::count
00000000002d22c0 B gazebo::common::Console::dbg
00000000002d23e0 B gazebo::common::Console::err
00000000002d2620 B gazebo::common::Console::log
00000000002d2500 B gazebo::common::Console::msg
00000000002d21a0 B gazebo::common::Console::warn
00000000002d2c20 B gazebo::common::Material::BlendModeStr
00000000002d2c40 B gazebo::common::Material::ShadeModeStr
00000000002d2c60 B gazebo::common::Material::counter
00000000002d2cd0 B gazebo::common::EnumIface<gazebo::common::MaterialType>::names
00000000002d2100 u SingletonT<gazebo::common::SystemPaths>::GetInstance()::t
00000000002d2db0 u SingletonT<gazebo::common::ModelDatabase>::GetInstance()::t
~~~

The static variables in
`Color`, `EnumIface`, `Image`, `Material`, `MaterialDensity`, and `Time`
are `const` or simple types.
The remaining variables will be addressed in the following subsections.

#### common::Console

~~~
00000000002d22c0 B gazebo::common::Console::dbg
00000000002d23e0 B gazebo::common::Console::err
00000000002d2620 B gazebo::common::Console::log
00000000002d2500 B gazebo::common::Console::msg
00000000002d21a0 B gazebo::common::Console::warn
~~~

The `dbg`, `err`, `msg` and `warn` variables are of type
`Console::Logger`, which inherits from `std::ostream`.
The `log` variable is of type `Console::FileLogger`, which also
inherits from `std::ostream`.
These variables exist for the duration of the program
and neither hold smart pointers nor provide smart pointers
to themselves.

#### common::Events

~~~
00000000002d2820 B gazebo::event::Events::postRender
00000000002d28a0 B gazebo::event::Events::worldReset
00000000002d27a0 B gazebo::event::Events::createSensor
00000000002d2920 B gazebo::event::Events::deleteEntity
00000000002d27c0 B gazebo::event::Events::removeSensor
00000000002d29a0 B gazebo::event::Events::worldCreated
00000000002d27e0 B gazebo::event::Events::diagTimerStop
00000000002d2980 B gazebo::event::Events::entityCreated
00000000002d2800 B gazebo::event::Events::diagTimerStart
00000000002d28c0 B gazebo::event::Events::worldUpdateEnd
00000000002d2900 B gazebo::event::Events::worldUpdateBegin
00000000002d2960 B gazebo::event::Events::setSelectedEntity
00000000002d28e0 B gazebo::event::Events::beforePhysicsUpdate
00000000002d2a00 B gazebo::event::Events::step
00000000002d29e0 B gazebo::event::Events::stop
00000000002d2a20 B gazebo::event::Events::pause
00000000002d2840 B gazebo::event::Events::render
00000000002d29c0 B gazebo::event::Events::sigInt
00000000002d2940 B gazebo::event::Events::addEntity
00000000002d2860 B gazebo::event::Events::preRender
00000000002d2880 B gazebo::event::Events::timeReset
~~~

#### common::SingletonT

This leaves the `SingletonT` types `ModelDatabase` and `SystemPaths`.
A third `SingletonT` type `MeshManager` is included in this library though it
didn't appear in the output from `nm`.

~~~
00000000002d2190 u guard variable for SingletonT<gazebo::common::SystemPaths>::GetInstance()::t
00000000002d2dc0 u guard variable for SingletonT<gazebo::common::ModelDatabase>::GetInstance()::t
00000000002d2d80 B gazebo::common::ModelDatabase::myself
00000000002d2100 u SingletonT<gazebo::common::SystemPaths>::GetInstance()::t
00000000002d2db0 u SingletonT<gazebo::common::ModelDatabase>::GetInstance()::t
~~~
