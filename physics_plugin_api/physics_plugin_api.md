## Project: TITLE
***Gazebo Design Document***

### Overview

To create a simple physics API for pluggable physics engines.

#### Motivation

Pluggable physics engine was motivated by:

1. It is difficult to maintain/release gazebo compiled against a different physics library.
  For example, during Gazebo-DART integration we had to deal with resolving dependency conflicts
  when compiling gazebo drcsim against DART.
1. The desire to integrate MuJoCo (Emo Todorov) and Moby (Evan Drumwright) with Gazebo by perspective authors.
1. Update existing physics API to make integration easier.
  Existing physics interface is multi-layered and complicated to integrate.
  New API proposed here should allow for fast and simple integration of very basic physics functionalities.
1. Old physics API is more ODE-centric, does not support both internal and maximal coordinate systems.
1. Old physics API is C++ based.  A C-style API will support more potential engines.

#### Approach

* Core design principle will be from the ground-up; i.e. to start with the simplest physics API possible,
  then extend it to support more sophisticated physics operations.
* We will not try to migrate existing physics engines (Bullet, DART, ODE, Simbody) into plugins.  Instead, we
  will continue to integrate and maintain these engines by hand.

### Requirements


### Architecture (System Diagram)


### Interfaces

#### Functions

### Performance Considerations

### Tests

### Related Pull Requests
