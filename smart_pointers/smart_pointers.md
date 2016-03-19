# Smart pointers in Gazebo (physics::World case)
***Gazebo Design Document***

## Overview

The purpose of this document is to provide guidelines for the way pointers and
smart pointers should be used in Gazebo. The specific use case focused here
will be the `physics::World` class.

## Current problem using `boost::shared_ptr`

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

A) Global API

B) Smart pointers

### Global API

Never store pointers to the world. Always call the global API
`physics::get_world()` to use it.

### Smart pointers

Since we've moved to C++11, we can stop using boost smart pointers and use
std smart pointers instead. Pointers to be considered:

| Pointer type      | Description                    | Use case | Drawbacks |
| ----------------- | ------------------------------ | -------- | --------- |
| `std::shared_ptr` | Shared ownership. Automatically deleted once all owners release it (`reset()`). | When we're not sure who is responsible for deleting the pointer. | Circular dependency. |
| `std::weak_ptr`   | Temporary ownership, own it by making it into a `std::shared_ptr` while using it (`lock()`), and release it immediately.     | When we have a clear owner of the pointer, but would like other classes to have access to it as well. The clear owner has a `shared_ptr` while other classes receive a `weak_ptr`. It solves the `shared_ptr` circular dependency issue.| Can be easily converted to a `shared_ptr` and stored by someone who shouldn't be owning it. |
| `std::unique_ptr` | Single ownership, which can be transfered (`move(ptr)`). Deleted when goes out of scope.     | When a pointer will only be used within a single scope. | Only one owner at a time, limited scope. |
| raw pointer      | No specific owners, someone must delete it.     | To be avoided. Acceptable uses would be when `new` and `delete` are called in a clear manner and the pointer is not shared in between (?) Or when using external APIs (?) | Someone must remember to delete it. |

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
shared pointers).

* If the pointer will be used by other classes, but not stored by them,
store in this class as a `unique_ptr` and pass raw pointers / references?
Then the users must know they should not delete the pointer.

* If the pointer is owned by this class, but ownership might be transfered to
other classes, that is, the pointer might outlive this class, store `shared_ptr`
and also pass as `shared_ptr`. (It may be the case that we don't really need
this usage in Gazebo, because we usually have a manager class.
`rendering::Visual`s for example can switch parents, but they all are contained
within `rendering::Scene`.)

#### Non-member pointers

* If the pointer will be limited to a scope, use `std::unique_ptr`.
For example, in
[`gui::MainWindow::Clone()`](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/gui/MainWindow.cc?fileviewer=file-view-default#MainWindow.cc-565)
a `CloneWindow` is created to live just within that scope.

* If the pointer is just being created, but will be owned by someone else,
(such as in a factory), use smart pointer appropriate to the class who will
receive it. If the receiving class might share it, pass as `shared_ptr`,
if it will keep it, pass as `unique_ptr`.

#### `physics::World` case

Many classes currently hold `shared_ptr`s to the `World` class, but in basically
all cases, it is not desirable that they have ownership of the world. They just
want to use the pointer from time to time.

For example, `sensors::Sensor` holds a pointer to the world, which it uses to
get things like the world name and the simulation time. It doesn't need to know
anything about the world's lifetime, just make sure the pointer is not null
before accessing it. So it would hold a `std::weak_ptr`.

All world pointers are created in
[`physics::PhysicsIface::create_world`](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/PhysicsIface.cc?fileviewer=file-view-default#PhysicsIface.cc-55)
and stored in the global variable [`g_worlds`](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/PhysicsIface.cc?fileviewer=file-view-default#PhysicsIface.cc-35). `g_worlds` should hold `shared_ptr`s to the world.


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

