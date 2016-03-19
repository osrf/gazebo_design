# Smart pointers in Gazebo (physics::World case)
***Gazebo Design Document***

## Overview

The main motivation for this document is to discuss the possible solutions
to some of the problems stemming from the way shared pointers are being
used in Gazebo. More specifically, this is meant to address the issues
involved in opening a new world within the same `gzserver` and properly
cleaning up the old world.

It is not the intent of this document to propose drastic changes to Gazebo's
architecture. Rather, it is to find the best possible short/mid term solution
which impacts users the least.

## Current problem: `boost::shared_ptr`

We make vast use of `boost::shared_ptr`s across all libraries in Gazebo. Though
safer than raw pointers when it comes to deciding when and who will delete them,
these pointers can bring circular dependency problems if used without caution,
and shouldn't be used in cases where multiple ownership of the pointer is not
needed.

Consider the case of classes `physics::World` and `physics::PhysicsEngine`.
Both these classes store a shared pointer of each other, see
[here](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/WorldPrivate.hh?fileviewer=file-view-default#WorldPrivate.hh-49)
and
[here](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/PhysicsEngine.hh?fileviewer=file-view-default#PhysicsEngine.hh-246).
This results in neither of their destructors ever being called, because one
class is waiting for the other to be destroyed first.

## Possible solutions

1. Hacky `Fini`

1. Global API

1. Smart[er] pointers

### 1. Hacky `Fini`

One way to resolve circular dependencies while keeping shared pointers is
to manually call `reset()` on pointers to release them when they're not
needed anymore.

Many classes in Gazebo have a member function called `Fini`, which clears
some of the internal state. In many cases, `Fini` and the destructor have
overlapping functionality. The approach here would be to:

1. Move all the calls from the destructor to `Fini`.

1. In the destructor, leave just a call to `Fini`.

1. Unlike the destructor, which is guaranteed to be called only once,
`Fini` is a public function which might be called several times. So
after moving the destructor's contents to `Fini`, we should make sure
pointers are checked before being accessed.

This approach started being implemented in a
[branch](https://bitbucket.org/osrf/gazebo/branches/compare/remove_blank_world%0Dgazebo7#chg-gazebo/physics/World.cc), with a
[test](https://bitbucket.org/osrf/gazebo/branches/compare/remove_blank_world%0Dgazebo7#chg-test/integration/world_remove.cc)
which checks that all `boost::shared_ptr<World>` were indeed released after
the `physics::remove_worlds()` call.

#### Advantages

No drastic changes to API or architecture.

#### Drawbacks

* Perpetuates a bad use of shared pointers. If an object is not supposed to
have multiple ownership, it shouldn't be shared.

* We're back with the problem of raw pointers, but instead of needing to choose
who will call delete, we're choosing who will call `Fini`.

### 2. Global API

This alternative is to never store pointers to the `World`.
Instead, each object can keep only a string with the name of the world,
and call the global function
[`physics::get_world(<name>)`](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/PhysicsIface.cc?fileviewer=file-view-default#PhysicsIface.cc-63)
to use it.

The
[`ServerFixture`](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/test/ServerFixture.cc?fileviewer=file-view-default)
class for example has a dozen calls to `get_world` instead of keeping
pointers.

#### Advantages

No drastic changes to API or architecture.

#### Drawbacks

Possible impact on performance due to string comparisons.

### Smart pointers

#### Overview

A proper way of fixing the issue might involve making better use of smart
pointers. Since we've moved to C++11, we can stop using boost smart pointers
and use std smart pointers instead. Pointers to be considered:

| Pointer type      | Description                    | Use case | Drawbacks |
| ----------------- | ------------------------------ | -------- | --------- |
| `std::shared_ptr` | Shared ownership. Automatically deleted once all owners release it (`reset()`). | When we're not sure who is responsible for deleting the pointer. | Circular dependency. |
| `std::weak_ptr`   | Temporary ownership, own it by making it into a `std::shared_ptr` while using it (`lock()`), and release it immediately.     | When we have a clear owner of the pointer, but would like other classes to have access to it as well. The clear owner has a `shared_ptr` while other classes receive a `weak_ptr`. It solves the `shared_ptr` circular dependency issue.| Can be easily converted to a `shared_ptr` and stored by someone who shouldn't be owning it. |
| `std::unique_ptr` | Single ownership, which can be transfered (`move(ptr)`). Deleted when goes out of scope.     | When a pointer will only be used within a single scope. | Only one owner at a time, limited scope. |
| raw pointer      | No specific owners, someone must delete it.     | When we know its lifetime is being handled by someone who will delete it. | Someone must remember to delete it. |

#### `physics::World` case

* When creating a world, keep a `unique_ptr` in `g_worlds` and pass a raw
pointer. This implies that `PhysicsIface` is the only one responsible for the
world's lifetime. Whoever wants to use it, can use a raw pointer but shouldn't
delete it. Example:

[Current](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/PhysicsIface.cc?fileviewer=file-view-default#PhysicsIface.cc-55):
~~~
physics::WorldPtr physics::create_world(const std::string &_name)
{
  physics::WorldPtr world(new physics::World(_name));
  g_worlds.push_back(world);
  return world;
}
~~~

New:
~~~
physics::World *physics::create_world(const std::string &_name)
{
  std::unique_ptr<physics::World> world(new physics::World(_name));
  g_worlds.push_back(world);
  return world.release();
}
~~~

* No changes should be needed in
[`physics::remove_worlds`](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/PhysicsIface.cc?fileviewer=file-view-default#PhysicsIface.cc-152),
and when the `unique_ptr` is reset, the world destructor will be called.

* Don't pass `shared_ptr<World>`. Example:

Current:
~~~
void physics::load_world(boost::shared_ptr<World> _world, sdf::ElementPtr _sdf)
{
  _world->Load(_sdf);
}
~~~

New:
~~~
void physics::load_world(World *_world, sdf::ElementPtr _sdf)
{
  _world->Load(_sdf);
}
~~~

* Don't store `shared_ptr<World>` in other classes.

1. Remove it whenever possible. For example, `physics::Contact` keeps a pointer
to the world just to access its name. We could keep the name string instead.

2. If the class will access it frequently and it's guaranteed that its lifetime
is shorter than the world, store a raw pointer. For example, `sensors::Sensor`
currently stores a `WorldPtr` and its derived classes use it frequently. Each
sensor only exists within a world, so they should be cleaned up before the
world. It should be safe to store a raw pointer.

3. Class might outlive the world, for example, `sensors::SensorManager` keeps a
list of world pointers. It would probably be ok to store world names instead.

#### Pull requests

1. Substitute `WorldPtr` with world name wherever it makes sense.

1. Change member `WorldPtr` to `*World` one class at a time.

1. Change `WorldPtr` to `*World` in functions one class at a time,
deprecating wherever necessary. (To keep the old functions working,
we'll probably need to make a `shared_ptr` from the raw pointer).

1. Change the `PhysicsIface` API and deprecate `WorldPtr` typedef.


































#### Migration

### Function deprecations

Shared pointers are widely used in our API, so any change to them will directly
affect user code. Ideally, we would be able to support both the old pointers and
the new pointers during one release (tick-tock release cycle) and remove the old
pointers in the subsequent release.

* For functions which take `shared_ptr` as input parameters, these functions
will be deprecated and equivalent functions using `weak_ptr` can be used.

* Functions which return `shared_ptr` can't be overloaded by different return
type, so their names will have to be slightly changed to accomodate.

### New typedefs

We currently use the `XPtr` typedef as shorthand for `boost::shared_ptr<X>`.
This obscured to the user the type of pointer being used. If the library will
start making better use of smart pointers and we expect users to also be mindful
of pointers, the types should be more explicit, even if more verbose.

The suggestion is to add different typedefs as needed:

* `XWeakPtr` for `std::weak_ptr<X>`
* `XSharedPtr` for `std::weak_ptr<X>`
* `XUniquePtr` for `std::unique_ptr<X>`

The different naming convention should also help avoiding collisions during the
deprecation cycle.

#### Pull requests

Transitioning to different smart pointers will touch all of Gazebo and thus
should be done slowly. The proposal is to begin with the `World` class and only
move on to other classes when that's complete.

The proposed order of pull requests is going from the leaves to the roots, so as
to keep changes as contained as possible. For example, rather than deprecating
all functions in `physics::PhysicsIface`, which would require changes
everywhere, deprecate it first in smaller classes like `physics::Contact`.

This will require some sort of mechanism to convert from `boost::shared_ptr` to
`std::shared_ptr`, such as
[this](http://stackoverflow.com/a/12605002),
so that the part of the API which is using boost can interact with the part
using std. This is analogous to the `Ign()` functions in `gazebo::math` created
to facilitate migration.

1. Create `WorldWeakPtr` and `WorldSharedPtr` typedefs. Implement boost<->std
conversion. Deprecations for a small class.

2~n. Deprecations for a class at a time.

n. Deprecate `WorldPtr` typedef.
















































#### Guidelines

##### Class member pointers

* If the pointer will only be used internally and should be deleted with the
parent object, store `unique_ptr`. For example, the private members `dataPtr`
from the PIMPL idiom.

* If the class received the pointer from somewhere else and just needs to
access it, but not own it or handle its lifetime, store `weak_ptr`. For
example, `sensors::Sensor`  holds a
[pointer](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/sensors/Sensor.hh?fileviewer=file-view-default#Sensor.hh-305)
to the world, which it uses to
get things like the world name and the simulation time. It doesn't need to know
anything about the world's lifetime, just make sure the pointer is not null
before accessing it. So it should store a `std::weak_ptr<World>`.

* If the pointer will be used by other classes but this class will
handle its deletion, store a `shared_ptr` and pass it to other classes as a
`weak_ptr`. For example, `physics::World` keeps a
[list](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/WorldPrivate.hh?fileviewer=file-view-default#WorldPrivate.hh-308)
of all `physics::Model` included in this world. It handles each model since its
[creation](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/World.hh?fileviewer=file-view-default#World.hh-433)
until its
[deletion](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/World.hh?fileviewer=file-view-default#World.hh-379).
The vector should be storing `std::shared_ptr<Model>`.
If other classes want access to the model pointers, the world can share
`std::weak_ptr<Model>` with them (currently it
[exposes](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/World.hh?fileviewer=file-view-default#World.hh-169)
shared pointers). Or:

* Alternatively to the previous point, if the pointer will be used by other
classes, but not stored by them, store it in this class as a `unique_ptr`
and pass raw pointers or references. The catch is that users must know they
should not delete the pointer.

Take as an example of what's done in Qt. Internally, classes may store
[smart pointers](http://code.qt.io/cgit/qt/qt.git/tree/src/gui/widgets/qpushbutton_p.h#n82),
while the API exposes them as
[raw pointers](http://code.qt.io/cgit/qt/qt.git/tree/src/gui/widgets/qpushbutton.cpp#n550).
This might be there by design or legacy, see
[this](http://stackoverflow.com/questions/10334511/why-do-c-libraries-and-frameworks-never-use-smart-pointers).

* If the pointer is owned by this class, but ownership might be transfered to
other classes, that is, the pointer might outlive this class, store `shared_ptr`
and also pass as `shared_ptr`. (It may be the case that we don't really need
this usage in Gazebo, because we usually have a manager class.
`rendering::Visual`s for example can switch parents, but all visuals are
managed by `rendering::Scene`.)

##### Input parameters

* Don't pass smart pointers unless you really want to take ownership.

*

##### Non-member pointers

* If the pointer will be limited to a scope, use `std::unique_ptr`.
For example, in
[`gui::MainWindow::Clone()`](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/gui/MainWindow.cc?fileviewer=file-view-default#MainWindow.cc-565)
a `CloneWindow` is created to live just within that scope.

* If the pointer is just being created, but will be owned by someone else,
(such as in a factory), use smart pointer appropriate to the class who will
receive it. If the receiving class might share it, pass as `shared_ptr`,
if it will keep it, pass as `unique_ptr`.
