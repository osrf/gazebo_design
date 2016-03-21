# Smart pointers in Gazebo (physics::World case)
***Gazebo Design Document***

## Overview

This document discusses the possible solutions to some of the problems stemming
from the way shared pointers are being used in Gazebo. More specifically, this
is meant to address the issues involved in opening a new world within the same
`gzserver` and properly cleaning up the old world.

It is not the intent of this document to propose drastic changes to Gazebo's
architecture. Rather, it is to find the best possible short/mid term solution
which impacts users the least.

## Current problem: `boost::shared_ptr`

We make vast use of `boost::shared_ptr`s across all libraries in Gazebo. Though
safer than raw pointers when it comes to deciding when and who will delete them,
these pointers can bring circular dependency problems if used without caution,
and ideally shouldn't be used in cases where multiple ownership of the pointer
is not needed.

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
to manually call `reset()` on pointers to release them when they're not needed anymore.

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

### 3. Smart[er] pointers

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

We'll consider two ways of using smart pointers:

A. `unique_ptr` + raw pointers

B. `shared_ptr` + `weak_ptr`

#### A. unique_ptr + raw pointers

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

##### Advantages

* Using raw pointers should be easier for API / ABI compatibility in the
future.

* No need to create extra typedefs.

##### Drawbacks

* Possible crashes if someone deletes the raw pointer.

* Lots of changes to the current API.

##### Pull requests

1. Substitute `WorldPtr` with world name wherever it makes sense.

1. Change member `WorldPtr` to `*World` one class at a time.

1. Change `WorldPtr` to `*World` in functions one class at a time,
deprecating wherever necessary. (To keep the old functions working,
we'll probably need to make a `shared_ptr` from the raw pointer).

1. Change the `PhysicsIface` API and deprecate `WorldPtr` typedef.

#### B. shared_ptr + weak_ptr

* This approach is very similar to the one above, except that we'd keep an
`std::shared_ptr` in `g_worlds` and pass `std::weak_ptr`s around. By design,
that should be the only `shared_ptr`, so it won't really be "shared".

##### Advantages

* Whoever gets the `weak_ptr` will unlikely have the impulse to delete it.

##### Drawbacks

* Will need extra typedefs.

* Lots of changes to the current API.

