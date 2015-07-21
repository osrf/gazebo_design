## Project: Physics Plugin and API Design
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

#### Initial Simulation Scenarios

Initial simulation scenarios to be built for the purpose of scoping out work for physics plugin API.

* Box resting on plane with contact under gravity.
* A simple pendulum connected to the inertial world.
* A pioneer 2dx robot.
* A simple arm model.

#### Open Questions

* Create a subset of API for multiplexing physics engines.  Potentially resource intensive, so we want to run this in the clouds.
* API for using engines to validate itself/other engines.  For example, we can run Simbody with different time step sizes to check temporal order of accuracy and numerical consistency.

### Requirements

* Provide a simple bare minimum API in C, reduce effort to plug a physics engine into gazebo.
* Provide a wrapper template example for building physics engine as a gazebo plugin.

### Architecture (System Diagram)

A very nice diagram.

### Existing Physics Interfaces

 *  High Level Physics Engine Initialization and Shutdown API:
     * [PhysicsEngine::Load](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-54): This function loads physics engine description from SDF without initializing the engine itself.
     * [PhysicsEngine::Init](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-57): Initialize underlying physics engine.
     * [PhysicsEngine::Reset](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-63)
     * [PhysicsEngine::Fini](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-60): Multi-step shutdown behavior.
     * [PhysicsEngine::InitForThread](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-66): Move this into Load or Init.  Prepare physics engine for multi-threaded access.

 * Entity Creation API:
     * [PhysicsEngine::CreateModel](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-110)
     * [PhysicsEngine::CreateLink](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-114)
     * [PhysicsEngine::CreateCollision](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-118)
     * [PhysicsEngine::CreateShape](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-130)
     * [PhysicsEngine::CreateJoint](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-136)

 * Runtime Modifications, Getters and Setters
     * [PhysicsEngine::SetSeed](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-77): Set seed of engine random seed.
     * [PhysicsEngine::SetTargetRealTimeFactor](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-97)
     * [PhysicsEngine::GetGravity](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-142)
     * we will deprecate anything that is not shared across all physics engines in `PhysicsEngine` class.  APIs such as `SetWorldCFM` will be shifted to string key-value parameter setters. 
     * ...
 
 * Operational API:
     * [PhyiscsEngine::UpdateCollision](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-69)
     * [PhysicsEngine::UpdatePhysics](https://bitbucket.org/osrf/gazebo/src/577847c43d021f7edc838a30c0eafc99ea312571/gazebo/physics/PhysicsEngine.hh?at=default#cl-108)

 * Runtime Functions
     * ...


### New Interface Proposal

Relevant Objects / Entities in Simulation:

 * Physics
 * World
 * Model
 * Link
   * Inertia
   * Visual
   * Collision
 * Joints

~~~
struct oppInertia
{
  std::string name;
  int id;
  double mass;
  matrix3 moi;
  matrix3 moi;
  Pose pose;
};

struct oppShape
{
};

struct oppSphereShape : public oppShape
{
};

struct oppBoxShape : public oppShape
{
};

struct oppCylinderShape : public oppShape
{
};

struct oppMeshShape : public oppShape
{
};

struct oppCollision
{
  std::string name;
  int id;
  Pose pose;
  Shape shape;
};

struct oppVisual
{
  std::string name;
  int id;
  Pose pose;
  Shape shape;
};

struct oppLink
{
  std::string name;
  int id;
  Pose pose;
  // pointer to arrays of objects
  oppInertia* inertias;
  oppCollision* collisions;
  oppVisual* visuals;
  oppJoint* parentJoints;
  oppJoint* childJoints;
  oppConstraint* constraints;
};

enum {
  oppJointTypeHinge         = 1,
  oppJointTypeSlider        = 2,
  oppJointTypeScrew         = 4
};

struct oppJoint 
{
  std::string name;
  int id;
  Pose pose;

  // hard = Featherstone, mobilizer, internal coordinate joint.
  // ~hard = soft = constraint based joint.
  bool hard;

  // type of joint: e.g. dxJointTypeHinge, etc.
  int jointType;

  // pointers to links
  oppLink* parentLinks;
  oppLink* childLinks;

  // joint info: ??? Jacobians, etc?
  JointInfo* data;
};

struct oppModel 
{
  oppLink* links;
  oppJoint* joints;
  Pose pose;
};

struct oppWorld 
{
  
};

struct oppPhysics
{
  
};


~~~

The API will be split into following categories:

 * Load: Initialization of different entities and components of simulation, e.g. Physics, World, Model, Link, etc.
 * Physics Engine Creation and Building:  E.g. GetParam/SetParam: Get and set model parameter.
 * Model Creation and Building:  For examples:
     1. CreateLink: create objects in simulation.
     1. GetParam/SetParam: Get and set model parameter.
 * Running simulation.

Details:

 * Simulation Initialization:
     1. PhysicsEngine::Load
     1. PhysicsEngine::Init
     1. PhysicsEngine::SetParam(key, value)
     1. PhysicsEngine::CreateWorld
     1. PhysicsEngine::World::Load
     1. PhysicsEngine::World::Init

 * Model Loading, Construction:
     1. PhysicsEngine::World::CreateModel
     1. PhysicsEngine::World::Model::CreateLink
     1. PhysicsEngine::World::Model::CreateJoint
     1. PhysicsEngine::World::Model::Link::Load
     1. PhysicsEngine::World::Model::Link::Init
     1. PhysicsEngine::World::Model::Joint::Load
     1. PhysicsEngine::World::Model::Joint::Init
     1. PhysicsEngine::World::Model::Link::SetParam

 * Run-time Modifications:
     1. PhysicsEngine::Step
     1. PhysicsEngine::World::Step
     1. PhysicsEngine::World::Model::Step

### Performance Considerations

* Calls that are invoked a lot, such as `MovedCallback` should be bufferred using dirty flags.

### Tests

* Find a way to run existing integration tests and regression tests against pluggable physics engines.

### Related Pull Requests

* None yet.  Starting with one for c-based template.
