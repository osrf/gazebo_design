# Undo / Redo user commands during simulation

## Overview

Users often wish to undo commands while editing their worlds in simulation. For
example, a user moves a robot from one place to another in the world but
afterwards wants to revert that command so the robot goes back to its previous
position.

![Simple case](https://bytebucket.org/osrf/gazebo_design/raw/undo/undo/simple_case.png)

The expected undo behaviour in a simple case like the one above is quite clear.
However, worlds in Gazebo are affected not only by user commands, but also by
the physics engine and plugins. Moreover, several clients might be connected to
the same simulation and be editing it at the same time. When all of these are
happening at the same time, it might not be so clear what is expected from the
undo command.

Let's look at a more complex example. We have a vehicle being controlled by a
plugin to drive between several cones.

1. The user moves the vehicle to the beginning of the course.

1. Then the plugin starts controlling it.

1. The vehicle hits a cone and the cone falls.

If the user hits undo now, what should happen?

![Plugins plus physics](https://bytebucket.org/osrf/gazebo_design/raw/undo/undo/cmd_plugin_physics.png)

The proposal here is that when the user presses "undo", the vehicle is moved to
the position it was before the user command, and also the cone goes back to its
standing position.

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
undone if the user command is undone. That is, *the world will go back to the
state it was before the user command*. Time however, does not go back.

* Future goal: plugin internal states are also rewinded. This could be done by
emitting events for undo / redo which plugins can listen to and each plugin is
responsible for handling it by themselves.

* Unlike undo, redo does not reproduce a whole world state. It only executes the
single user command which was executed previously and physics/plugins work as
usual from there.

## Architecture

### Keyframes (world states)

In order to return the world to the state it was before a user command, we need
to keep track of "keyframes", or complete world states. A keyframe would contain
pose, (velocity and acceleration ?) for all entities in the world at a given
time.

Therefore, each time a command is executed, a keyframe is added to the undo
queue. This has the potential of decreasing performance, so we will probably
need to limit the number of keyframes stored (maximum number of undo steps).

The world class keeps a pointer to the whole SDF description of the scene. So
a function like this could be added to `physics::World`.

> "Keyframe" functionality sounds similar to what is currently performed by the
`WorldState` class. To my best understanding so far, `WorldState` handles
incremental changes exclusively, so a state only describes things that have
changed since the previous time step. During the implementation, it might make
more sense to extend the `WorldState` class to handle complete sets of
information instead of introducing the concept of "keyframes".

    /// \brief Gets an SDF element with the complete description of the world.
    sdf::ElementPtr World::Keyframe()
    {
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
      public: UserCmd() {};

      /// \brief Destructor
      public: virtual ~UserCmd() {};

      /// \brief This performs the user command.
      public: virtual void Do() = 0;

      /// \brief This performs the opposite of the user command. For most cases,
      /// it will involve loading a keyframe.
      public: virtual void Undo() = 0;

      /// \brief SDF representing the whole world state the moment the user
      /// command was executed. The default behaviour of "Undo" will be to set
      /// the world to this state by default.
      private: sdf::ElementPtr keyframe;
    };




