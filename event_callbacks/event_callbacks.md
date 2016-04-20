## Project: Event callbacks
***Gazebo Design Document***

### Overview

This is an attempt to document the existing infrastructure in gazebo
for registering callback functions that can be triggered by events.
It also analyzes the object lifecycle and ownership patterns
to determine if the current pointer types are appropriate.

### Requirements

1. A set of classes that allow functions to be registered as callback functions
that will be called when an event is signaled.
These classes should include a mechanism for un-registering callbacks.

2. An set of events relevant to Gazebo's functionality with
callback arguments should be defined.
It should be possible to define other events as well.

3. Callbacks should be able to be registered from different threads.
Signalling the event will block until all the callback functions
have been executed.

4. The callbacks can have arbitrary input parameters
but should all return `void`.

### Architecture

A cartoon diagram of an event is shown below.
The event is drawn as a box with a slot for inserting function pointers,
a trap door for removing them,
and a button at the top that will execute all the callbacks in the box
when it is pushed.
When a callback is added using `Connect`, an `id` is returned.
This `id` is needed to remove the callback using `Disconnect`.

![event interface diagram](event_callbacks.png)

### Interfaces

There are numerous classes currently involved in the interface
for registering and signaling event callbacks.
There is a base class `Event` and a derived class `EventT`
that is templated on the callback function signature,
which includes input paramters.
The `Connection` class is used as the return type of the
`EventT::Connect` interface.
The callback can then be removed by passing this object to the
`Event::Disconnect` interface
or by deleting the `Connection` object.

~~~
class Event
{
  public: Event();
  public: virtual ~Event();
  public: virtual void Disconnect(ConnectionPtr _c) = 0;
  public: virtual void Disconnect(int _id) = 0;
};
~~~

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
