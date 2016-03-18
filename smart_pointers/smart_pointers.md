## Smart pointers in Gazebo (physics::World case)
***Gazebo Design Document***

### Overview

The purpose of this project is to standardize the way pointers and smart i
pointers are used in Gazebo. The specific use case focused here is the
`physics::World` class.

### Current problem using `boost::shared_ptr`

We make vast use of `boost::shared_ptr`s across all libraries in Gazebo. Though
safer than raw pointers in many cases, these pointers can bring circular
dependency problems if we're not careful about them, and we have not being.

Consider the case of classes `physics::World` and `physics::PhysicsEngine`.
Both these classes store a shared pointer of each other, see
[here](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/WorldPrivate.hh?fileviewer=file-view-default#WorldPrivate.hh-49)
and
[here](https://bitbucket.org/osrf/gazebo/src/d3b06088be22a15a25025a952414bffb8ff6aa2b/gazebo/physics/PhysicsEngine.hh?fileviewer=file-view-default#PhysicsEngine.hh-246).
This results in neither of their destructors being called, as both shared
pointers would need to be released at the same time.

### Smart pointers

No matter what we do, we should stop using boost smart pointers and start using
std smart pointers, since we moved to C++11. The pointers we should consider:

| Pointer type      | Description                    | Use case |
| ----------------- | ------------------------------ | -------- |
| `std::shared_ptr` | Shared ownership. Automatically deleted once all owners release it (`reset()`). | When we're not sure who is responsible for deleting the pointer. |
| `std::weak_ptr`   | Temporary ownership, own it by making it into a `std::shared_ptr` while using it (`lock()`), and release it immediately.     | When we have a clear owner of the pointer, but would like other classes to have access to it as well. The clear owner has a `shared_ptr` while other classes receive a `weak_ptr`. |
| `std::unique_ptr` | Single ownership, which can be transfered (`move(ptr)`).     | When a pointer will only be used within a single scope. For example, the private members `dataPtr` from the PIMPL idiom. |
| raw pointer      | No specific owners, someone must delete it.     | To be avoided. Acceptable uses would be when `new` and `delete` are called in a clear way and the pointer is not shared? Or when using external APIs? |

The problem of circular dependencies is handled by using `weak_ptr`s.

### Guidelines

## Class member pointers

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

### `physics::World`

Many classes currently hold `shared_ptr`s to the `World` class, but it is not desirable that they have ownership of this world.



