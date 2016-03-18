## Smart pointers in Gazebo (physics::World case)
***Gazebo Design Document***

### Overview

The purpose of this project is to standardize the way pointers and smart
pointers are used in Gazebo. The specific use case focused here is the
`physics::World` class.

### Current problem using `boost::shared_ptr`

We make vast use of `boost::shared_ptr`s across all libraries in Gazebo. Though
safer than raw pointers when it comes to being deleted, these pointers can bring
circular dependency problems if used without caution, as is currently done in
several places.

Consider the case of classes `physics::World` and `physics::PhysicsEngine`.
Both these classes store a shared pointer of each other, see
[here](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/WorldPrivate.hh?fileviewer=file-view-default#WorldPrivate.hh-49)
and
[here](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/PhysicsEngine.hh?fileviewer=file-view-default#PhysicsEngine.hh-246).
This results in neither of their destructors being called, because one class is
waiting for the other to be destroyed first.

### Smart pointers

Since we've moved to C++11, we can stop using boost smart pointers and use
std smart pointers instead. Pointers to be considered:

| Pointer type      | Description                    | Use case | Drawbacks |
| ----------------- | ------------------------------ | -------- | --------- |
| `std::shared_ptr` | Shared ownership. Automatically deleted once all owners release it (`reset()`). | When we're not sure who is responsible for deleting the pointer. | Circular dependency. |
| `std::weak_ptr`   | Temporary ownership, own it by making it into a `std::shared_ptr` while using it (`lock()`), and release it immediately.     | When we have a clear owner of the pointer, but would like other classes to have access to it as well. The clear owner has a `shared_ptr` while other classes receive a `weak_ptr`. It solved the `shared_ptr` circular dependency issue.| Can be easily converted to a `shared_ptr` and stored by someone who shouldn't be owning it. |
| `std::unique_ptr` | Single ownership, which can be transfered (`move(ptr)`). Deleted when goes out of scope.     | When a pointer will only be used within a single scope. For example, the private members `dataPtr` from the PIMPL idiom. | Only one owner at a time, limited scope. |
| raw pointer      | No specific owners, someone must delete it.     | To be avoided. Acceptable uses would be when `new` and `delete` are called in a clear way and the pointer is not shared? Or when using external APIs? | Someone must remember to delete it. |

### Guidelines

#### Class member pointers

* If the pointer will only be used internally and should be deleted with the
parent object, use `unique_ptr`.

* If the class received the pointer from somewhere else and just needs to
access it, but not own it or handle its lifetime, use `weak_ptr`.

* If the pointer will be used by other classes but we're the ones who will
handle its deletion, use `shared_ptr` and pass it to other classes as a
`weak_ptr`.

* If the pointer is owned by this class, but ownership might be transfered to
other classes, that is, the pointer might outlive this class, use `shared_ptr`
and pass `shared_ptr`.

### Non-member pointers

* If the pointer will be limited to a scope, use `std::unique_ptr`.

* If the pointer is just being created, but will be owned by someone else, use
type according to the class member pointers above which apply to the receiver.

### `physics::World` case

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


### Migration

## Function deprecations

Shared pointers are widely used in our API, so any change to them will directly
affect user code. Ideally, we would be able to support both the old pointers and
the new pointers during one release (tick-tock release cycle) and remove the old
pointers in the subsequent release.

* For functions which take `shared_ptr` as input parameters, these functions
will be deprecated and equivalent functions using `weak_ptr` can be used.

* Functions which return `shared_ptr` can't be overloaded by different return
type, so their names will have to be slightly changed to accomodate.

## New typedefs

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

### Pull requests

Transitioning to different smart pointers will touch all of Gazebo and thus
should be done slowly. The proposal is to begin with the `World` class and only
move on to other classes when that's complete.

The proposed order of pull requests is going from the leaves to the roots, so as
to keep changes as contained as possible. For example, rather than deprecating
all functions in `physics::PhysicsIface`, which would require changes
everywhere, deprecate it first in smaller classes like `physics::Contact`.

This will require some sort of mechanism to convert from `boost::shared_ptr` to
`std::shared_ptr`, such as
[this](http://stackoverflow.com/a/12605002).

1. Create `WorldWeakPtr` and `WorldSharedPtr` typedefs. Implement boost<->std
conversion. Deprecations for a small class.

2~n. Deprecations for a class at a time.

n. Deprecate `WorldPtr` typedef.

