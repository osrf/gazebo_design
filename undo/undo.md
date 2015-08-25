# Undo / Redo user commands during simulation

## Overview

Users often wish to undo commands while editing their worlds in simulation. For
example, a user moves a robot from one place to another in the world but
afterwards wants to revert that command so the robot goes back to its previous
position.

![Simple case](https://bytebucket.org/osrf/gazebo_design/raw/undo/undo/simple_case.png)

The expected undo behaviour in a simple case like the one above is quite clear.
However, worlds in Gazebo are affected not only by user commands, but also by
the **physics engine** and **plugins**. Moreover, several clients might be
connected to the same simulation and be editing it at the same time. When all of
these are happening at the same time, it might not be so clear what is expected
from the undo command.

Let's look at a more complex example. We have a vehicle being controlled by a
plugin to drive between several cones.

1. The user moves the vehicle to the beginning of the course (cmd).

1. Then the vehicle starts being controlled by a plugin.

1. The vehicle hits a cone and the cone falls.

If the user hits undo now, what should happen?

![Plugins plus physics](https://bytebucket.org/osrf/gazebo_design/raw/undo/undo/cmd_plugin_physics.png)

The proposal here is that when the user presses "undo", the vehicle is moved to
the position it was before the user command, and also the cone goes back to its
previous pose.

![Proposal](https://bytebucket.org/osrf/gazebo_design/raw/undo/undo/proposal.png)

## Specifications

* Undo user commands, but not pure plugin / physics actions.

* User commands which can be undone:

    + Translate

    + Rotate

    + Scale

    + Snap

    + Align

    + Insert / paste entity

    + Delete entity

    + Copy entity

    + Any others?

* All physics / plugin effects which happened after a user command will be
undone if the user command is undone. That is, **the world will go back to the
state it was before the user command**. Time however, does not go back.

* Future goal: plugin internal states are also rewinded. This could be done by
emitting events for undo / redo which plugins can listen to and each plugin is
responsible for handling it by themselves.

* Unlike undo, **redo** does not reproduce a whole world state. It only executes the
single user command which was executed previously and physics/plugins work as
usual from there.

## Architecture

### Keyframes (world states)

In order to return the world to the state it was before a user command, we need
to keep track of "keyframes", i.e. complete world states. A keyframe would contain
pose and velocity information for all entities in the world at a given time. (An
open question is whether this information is sufficient or do we need to also
keep track of things like forces).

Therefore, each time a command is executed, a keyframe is added to the undo
queue. This has the potential of decreasing performance, so we will probably
need to limit the number of keyframes stored (maximum number of undo steps).

> "Keyframe" functionality sounds similar to what is currently performed by the
`WorldState` class. To my best understanding so far, `WorldState` handles
incremental changes exclusively, so a state only describes things that have
changed since the previous time step. During the implementation, it might make
more sense to extend the `WorldState` class to handle complete sets of
information instead of introducing the concept of "keyframes".

The world class keeps a pointer to the whole SDF description of the scene. So
functions like these might be added to `physics::World`.

    /// \brief Gets an SDF element with the complete description of the world.
    /// \return The complete SDF for the current state of the world.
    sdf::ElementPtr World::Keyframe()
    {
      // Note issue #1714
      this->dataPtr->sdf->Update();
      return this->dataPtr->sdf;
    }

    /// \brief Set the complete state of the world.
    /// \param[in] SDF describing the entire world.
    void World::SetKeyframe(sdf::ElementPtr _sdf)
    {
      // Update the state of all entities in the world
    }

### User commands

There will be a pure virtual class called `gui::UserCmd`, with `Do` and `Undo`
functions:

    /// \brief Base class which represents a user command, which can be "done"
    /// and "undone".
    class UserCmd
    {
      /// \brief Constructor
      public: UserCmd(sdf::ElementPtr _keyframe) : keyframe(_keyframe)
      {
      };

      /// \brief Destructor
      public: virtual ~UserCmd() {};

      /// \brief This performs the user command.
      public: virtual void Do() = 0;

      /// \brief This performs the opposite of the user command. For most cases,
      /// it will involve loading a keyframe.
      /// Note: Instead of being abstract, this could have a default
      /// implementation which sets the keyframe to the world.
      public: virtual void Undo() = 0;

      /// \brief Pointer to the world
      private: physics::WorldPtr world;

      /// \brief SDF representing the whole world state the moment the user
      /// command was executed. The default behaviour of "Undo" will be to set
      /// the world to this state by default.
      private: sdf::ElementPtr keyframe;
    };

Each user command will inherit from this class and implement its own functions.
Here's an example for a general command which changes a model's pose, such as
`translate`, `rotate`, `snap` and `align`:

    /// \brief A user command which alters the pose of an entity in the world.
    class MoveEntityCmd : public UserCmd
    {
      /// \brief Constructor
      /// \param[in] _keyframe SDF representing the whole world state the
      /// moment the command was executed.
      /// \paramp[in] _entity Entity which was moved, such as a model or a
      /// light.
      /// \param[in] _endPose End pose
      public: MoveEntityCmd(physics::WorldPtr _world, sdf::ElementPtr _keyframe,
          physics::EntityPtr _entity,
          ignition::math::Pose3d _endPose)
          : world(_world), keyframe(_keyframe), entity(_entity), endPose(_endPose)
      {
      };

      /// \brief Destructor
      public: ~MoveEntityCmd() = default;

      /// \brief Set the entity's pose to be the end pose.
      public: void Do()
      {
        this->entity->SetPose(endPose);
      };

      /// \brief Set the world state to be that of before the user moved the
      /// entity.
      public: void Undo()
      {
        this->world->SetKeyframe(this->keyframe);
      };

      /// \brief Entity which was moved.
      private: physics::EntityPtr _entity;

      /// \brief Pose which the user has moved the entity to.
      private: ignition::math::Pose3d endPose;
    };

### Command queue

Since all user commands inherit from the same class, they can be kept in two
queues, one for **undo** and another for **redo**. The queues are



