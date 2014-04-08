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
* Reference OpenGL API for style.
* Create an OpenPL repository for implementing new physics plugin.

An initial simulation scenarios described below will be constructed:

* Box resting on plane with contact under gravity.
* A simple pendulum connected to the inertial world.
* A pioneer 2dx robot.
* A simple arm model.

#### Open Questions

### Requirements


### Architecture (System Diagram)


### Interfaces

#### Existing High Level Physics Engine Initialization and Shutdown API:

 * [PhysicsEngine::Load](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-54): This function loads physics engine description from SDF without initializing the engine itself.
 * [PhysicsEngine::Init](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-57): Initialize underlying physics engine.
 * [PhysicsEngine::Reset](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-63)
 * [PhysicsEngine::Fini](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-60): Multi-step shutdown behavior.
 * [PhysicsEngine::InitForThread](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-66): Move this into Load or Init.  Prepare physics engine for multi-threaded access.


#### Existing Entity Creation API:

 * CreateModel
 * CreateLink
 * CreateCollision
 * CreateShape
 * CreateJoint

#### Existing Runtime Modifications, Getters and Setters

 * [PhysicsEngine::SetSeed](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-77): Set seed of engine random seed.
 * [PhysicsEngine::SetTargetRealTimeFactor](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-97)
 * GetGravity
 * ...
 
#### Existing Operational API:

 * [PhyiscsEngine::UpdateCollision](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-69)
 * [PhysicsEngine::UpdatePhysics](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-108)

#### Existing Runtime Functions

### Performance Considerations

### Tests

### Related Pull Requests
