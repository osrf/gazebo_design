# Undo / Redo user commands during simulation

## Overview

Users often wish to undo commands while editing their worlds in simulation. For
example, a user moves a robot from one place to another in the world but
afterwards wants to revert that command so the robot goes back to its previous
position.

![Simple case](https://bytebucket.org/osrf/gazebo_design/raw/undo/undo/simple_case.png)

The expected undo behaviour in a simple case like the one above is quite clear.
However, worlds in Gazebo are affected not only by user commands, but also by
the **physics engine** and **plugins**. Moreover, **several clients** might be
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

Different users might expect different behaviours from undo here. Such as:

1. The **vehicle returns** to its previous position before the user moved it, and
**also the cone** gets back standing up, as it was a side effect of moving the car.

1. The **vehicle returns** to its previous position but all side-effects remain
unchanged, so the cone remains fallen.

1. Some users might expect that undo would **just restore the cone's pose**,
since that's the last thing that "happened".

### Current proposal

This document proposes option 1, because we imagine it might be more useful to i
users. If moving the car was a mistake, so were the side-effects of moving it.

![Proposal](https://bytebucket.org/osrf/gazebo_design/raw/undo/undo/proposal.png)

* **Undo** will be treated as **going back in time**, instead of simply
executing the inverse of the user command.

* Going back in time means there's no need to keep track of what happened
directly as a consequence of the user's command - everything is rewinded. This
might have consequences unforeseen by the user, because actions which had nothing
to do with their command, such as other robots moving in the scene, will also
be undone.

* **Redo** will jump forward to the moment the user hit undo. This way, the
user can "undo the undo" if they wish.

* Things might get confusing for multiple clients, as going back in time will
affect all connected clients. This could be made clearer using GUI notifications
to tell other clients what's going on.

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

* Time jumps back and forth as the user undoes / redoes.

* If a log is being recorded, it continues to be recorded normally even if undo
has been triggered.

    + The jump in time will be recorded in the log file.

    + During log playback, the user will see the time jumping in the timeline.

    + If during playback, the user seeks to a time which is duplicated in the file,
      they are taken to the first sample that has that time.

* Plugins which make use of time might be affected by the jump back in time and
the jump in positions of models which they didn't expect to move.

For example, a plugin is using a custom PID control to move a robot arm to grasp
an object. The user moves the object and hits undo to move it back. The robot
moves back and so does the time. The plugin will likely go crazy.

Hopefully, users which want to use undo often while their plugins are running
will be willing to solve these problems from within the plugin.

## Architecture

### Keyframes (world states)

In order to return the world to the state it was before a user command, we need
to keep track of "keyframes", i.e. complete world states. A keyframe would contain
pose and velocity information for all entities in the world at a given time (which
should be sufficient to fully restore all physics states).

Therefore, each time a command is executed, a keyframe is added to the undo
queue. This has the potential of decreasing performance and making user
interaction laggy on smaller computers. We will probably need to limit the
number of keyframes stored (maximum number of undo steps). Perhaps also give
the user an option to turn off the undo feature.

> "Keyframe" functionality sounds similar to what is currently performed by the
`WorldState` class. To my best understanding so far, `WorldState` handles
incremental changes exclusively, so a state only describes things that have
changed since the previous time step. During the implementation, it might make
more sense to extend the `WorldState` class to handle complete sets of
information instead of introducing the concept of "keyframes".

The world class keeps a pointer to the whole SDF description of the scene. A
couple of functions such as follows might be added to `physics::World`.

    /// \brief Gets an SDF element with the complete description of the world.
    /// \return The complete SDF for the current state of the world.
    sdf::ElementPtr World::Keyframe()
    {
      // Note issue #1714
      // It will go somewhat like this...
      this->dataPtr->sdf->Update();
      this->UpdateStateSDF();
      return this->dataPtr->sdf;
    }

    /// \brief Set the complete state of the world.
    /// \param[in] SDF describing the entire world.
    void World::SetKeyframe(sdf::ElementPtr _sdf)
    {
      // Update the state of all entities in the world
    }

### User commands

Some information about user commands will be kept in the server side, and thus
be shared among all clients, while some information will be client-specific.

#### Server side

The structure kept server-side will keep information about the world state
(keyframes).

The server knows:

* The state of the world before the command was executed.

* If undo is executed, store the state of the world the moment undo was
executed so it can be used by redo.

* A unique ID for the command.

* A descriptive name for the command, such as "Translate unit_box" or
"Delete unit_box".

Add a class for user commands, `physics::UserCmd`, with ``Undo` and `Redo`
functions. Each command executed will create an object of this class:

    /// \brief Class which represents a user command, which can be "undone"
    /// and "redone".
    class UserCmd
    {
      /// \brief Constructor
      /// \param[in] _ID Unique ID for this command
      /// \param[in] _world Pointer to the world
      public: UserCmd(std::string _ID,
                      physics::WorldPtr _world,
                      const std::string &_description)
          : ID(_ID), world(_world), description(_description)
      {
        this->startState = this->world->Keyframe();
      };

      /// \brief Destructor
      public: virtual ~UserCmd() {};

      /// \brief Set the world state to the one just before the user command.
      public: virtual void Undo()
      {
        // Record / override the current state for redo
        this->endState = this->world->Keyframe();

        // Set the world state
        this->world->SetKeyframe(this->startState);
      }

      /// \brief Set the world state to be that of the moment undo was last
      /// called.
      public: virtual void Redo()
      {
        // We don't update startState even if some time has passed since undo...?

        // Set the world state
        this->world->SetKeyframe(this->endState);
      }

      /// \brief Return this command's unique ID.
      /// \return Unique ID
      public: std::string ID()
      {
        return this->ID
      };

      /// \brief Pointer to the world
      private: physics::WorldPtr world;

      /// \brief SDF representing the whole world state the moment the user
      /// command was executed.
      private: sdf::ElementPtr startState;

      /// \brief SDF representing the whole world state for the most recent
      /// time the user has triggeded undo for this command.
      private: sdf::ElementPtr endState;

      /// \brief Unique ID identifying this command in the server. It is set by
      /// the client which generated the user command, so we must find a way to
      /// avoid collisions.
      private: std::string ID;

      /// \brief Description for the command.
      private: std::string description;
    };

Whenever the user performs a command, the **client publishes a `UserCmd`**
message. For example:

    package gazebo.msgs;

    /// \ingroup gazebo_msgs
    /// \interface UserCmd
    /// \brief Notifies that a new command has been executed by a user

    message UserCmd
    {
      /// \brief Unique id for user command.
      required string id = 1;

      /// \brief Description for the command.
      required string description = 2;
    }

On the server side, a `physics::UserCmdManager` class will subscribe to
`UserCmd` messages. It will keep two lists of `UserCmd` objects: one for undo,
another for redo.

When the server receives a new command message, it creates a `UserCmd` object and
appends it to the end of the `undoUserCmds` vector.

    /// \brief Callback when a UserCmd message is received.
    /// \param[in] _msg Incoming message
    private: void UserCmdManager::OnMoveEntityCmd(msgs::MoveEntityCmdPtr _msg)
    {
      EntityPtr entity = this->world->GetEntity(_msg->name());
      MoveEntityCmd cmd = new MoveEntityCmd(msgs::Convert(
          _msg->time()),
          this->world,
          this->world->Keyframe,
          entity,
          _msg->end_pose());

      // Add it to undo list
      this->userUndoCmds.push_back(cmd);

      // Clear redo list
    };

The server does / undoes a command when it receives a message with the command's
unique ID and whether it should be done or undone. The message will look like
this:

    package gazebo.msgs;

    /// \ingroup gazebo_msgs
    /// \interface UndoRedo
    /// \brief Message for doing / undoing a user command

    import "time.proto";

    message UndoRedo
    {
      /// \brief Unique id for user command.
      required Time id = 1;

      /// \brief True to undo, false to redo.
      required bool undo = 2;
    }

And the subscriber callback:

    /// \brief Callback when an UndoRedo message is received.
    /// \param[in] _msg Incoming message
    private: void UserCmdManager::OnUndoRedoMsg(msgs::UndoRedoPtr _msg)
    {
      // Undo
      if (_msg()->undo())
      {
        // Check if msg id is found in the undo vector

        // Maybe check it is indeed the last command by that gzclient in the
        // list?

        // Get the command
        UserCmd *cmd = this->userRedoCmds.back();

        // Do it
        cmd->Do();

        // Remove from redo list
        this->userRedoCmds.pop_back();

        // Add command to undo list
        this->userUndoCmds.push_back(cmd);
      }
      // Redo
      else
      {
        // similar to undo
      }
    };

#### Client side





### Command queue





Since all user commands inherit from the same class, they can be kept in two
queues, one for **undo** and another for **redo**. The queues are


### Open questions

1. Someone hits Ctrl+Z by mistake after 10 mins of simulation and suddenly
everything changes...?




