# Undo / Redo user commands during simulation

## Overview

Users often wish to undo commands while editing their worlds in simulation. For
example, a user moves a model from one place to another in the world but
afterwards wants to revert that command so the model goes back to its previous
position.

![Simple case](https://bytebucket.org/osrf/gazebo_design/raw/undo_2.0/undo/simple_case.png)

### What would undo do?

The expected undo behaviour in a simple case like the one above is quite clear.
However, worlds in Gazebo are affected not only by user commands, but also by
the **physics engine** and **plugins**. Moreover, **several clients** might be
connected to the same simulation and be editing it at the same time. When all of
these are happening at the same time, it might not be so clear what is expected
from the undo command.

Let's look at a more complex example. We have a vehicle being controlled by a
plugin to drive between several cones.

1. The user moves the vehicle to the beginning of the course (cmd).

1. The vehicle starts being controlled by a plugin.

1. The vehicle hits a cone and the cone falls.

If the user hits undo now, what should happen?

![Plugins plus physics](https://bytebucket.org/osrf/gazebo_design/raw/undo_2.0/undo/cmd_plugin_physics.png)

Different users might expect different behaviours from undo here. Such as:

1. The **vehicle returns** to its previous position before the user moved it, and
**also the cone** gets back standing up, as it was a side effect of moving the car.
This would be effectively going back in time to the moment just before the user
command. All models would retain their physical states, such as velocity.

1. The **vehicle returns** to its previous position but all side-effects remain
unchanged, so the cone remains fallen. The vehicle's physical states are reset.

1. **Just restore the cone's pose**, since that's the last thing that
"happened".

### Current proposal

This document proposes option 2, i.e. return the vehicle but not the cone, for
a few reasons:

* **Undo** will be treated as an **inverse command** instead of a **going back in
time**. Going back in time could be introduced as a new feature where the user
saves "keyframes" of the simulation in case they want to go back to a specific
configuration.

* This way, it is always predictable what undo will do. Going back in time
might have unexpected effects such as undoing other things that happened due to
physics / plugins / other clients, which maybe didn't even interact with the
user command.

* Supporting multiple clients will be more natural, as one client undoing their
actions won't affect what the other client did, unless they are commanding the
same model. In case they are acting on the same model, undo commands will be
handled like other user commands are being handled at the moment: they are
executed in order.

## Specifications

* User commands which can be undone:

    + **Translate / Rotate / Snap / Align ("move" commands)**:

      > **Undo** restores the full pose before the command. For example, if the
      model tips over after being translated (position only), it is translated
      back with the same full pose (position and orientation) as before, not
      the new orientation.

      > **Redo** restores the full pose the model got to the first time the model
      was moved. For example, model A is aligned to model B, then this is
      undone, then model B moves. If the user hits redo now, model A will
      move to the way it was previously aligned, instead of being aligned to
      model B's new pose. This is done to keep undo and redo invertible,
      foreseeable and locally repeatable.

      ![Move proposal](https://bytebucket.org/osrf/gazebo_design/raw/undo_2.0/undo/proposal_move.png)

    + **Scale**:

      > **Undo** restores the scale before the command. Any other coupled effects such
      as scaling inertias and mass should also be undone.

      > **Redo** scales the same way the user did before.

    + **Insert / paste entity**:

      > **Undo** deletes the entity. If pasting a copied entity, the entity remains
      in the copy stack ready to be pasted again.

      > **Redo** spawns a new entity with the same name, but probably different ID.
      The spawned model should appear in the pose the previous model was at.

    + **Delete entity**:

      > **Undo**: See redo above.

      > **Redo**: See undo above.

* New commands are added to the end of a **list of undo commands**. Commands are
undone starting from the end of the list.

* Undone commands are added to the end of a **list of redo commands**. Commands
are redone starting from the end of the list. When the user executes a new
command, the redo list is cleared.

* The user might try to undo something which isn't possible anymore, such as
moving something which a plugin deleted. Some possible outcomes are:

    + Clear that client's whole lists.

    + Display a warning that it wasn't undone but keep lists.

* There will be undo and redo buttons on the top toolbar, with `Ctrl+Z` and
`Shift+Ctrl+Z` hotkeys respectively. There will also be items under the `Edit`
menu.

* Nice to have: Long-pressing the undo / redo toolbar buttons displays the list
of commands and the user can press any command to execute all commands leading
to it.

## Architecture

### User commands

All information about user commands will be kept in the client side.

There will be an abstract class `gui::UserCmd`, with `Do` and `Undo`
functions to be overridden:

    /// \brief Base class which represents a user command that can be "done"
    /// and "undone".
    class UserCmd
    {
      /// \brief Constructor
      public: UserCmd() {};

      /// \brief Destructor
      public: virtual ~UserCmd() {};

      /// \brief This performs the user command.
      /// \return True if successul.
      public: virtual bool Do() = 0;

      /// \brief This performs the opposite of the user command.
      /// \return True if successul.
      public: virtual bool Undo() = 0;
    };

Each user command will inherit from this class and implement its own functions.
Here's an example for a general command which changes a model's pose, such as
`translate`, `rotate`, `snap` and `align`.

For the server, there's no difference between a "move" command and an "undo
move" command.

    /// \brief A user command which alters the pose of a model in the world.
    class MoveModelCmd : public UserCmd
    {
      /// \brief Constructor
      /// \paramp[in] _modelName Scoped name of model which was moved.
      /// \param[in] _startPose Start pose
      /// \param[in] _endPose End pose
      public: MoveModelCmd(std::string _modelName
                           ignition::math::Pose3d _startPose,
                           ignition::math::Pose3d _endPose)
          : modelName(_modelName),
            endPose(_startPose),
            endPose(_endPose)
      {
      };

      /// \brief Destructor
      public: ~MoveModelCmd() = default;

      /// \brief Set the model's pose to be the end pose.
      /// \return True if successul.
      public: bool Do()
      {
        // Check if model still exists

        // Publish message to move to end pose

        // Optional: check after a while to see if succeeded
      };

      /// \brief Set the model's pose to be the start pose.
      /// \return True if successul.
      public: bool Undo()
      {
        // Check if model still exists

        // Publish message to move to start pose

        // Optional: check after a while to see if succeeded
      };

      /// \brief Name of model which was moved.
      private: std::string modelName;

      /// \brief Pose which the model had before being moved.
      private: ignition::math::Pose3d startPose;

      /// \brief Pose which the user has moved the model to.
      private: ignition::math::Pose3d endPose;
    };

### User command manager

The lists of commands will be handled by class `gui::UserCmdManager`.
When the manager receives a new command, it creates a `UserCmd` object and
appends it to the end of the `undoUserCmds` vector.

    /// \brief User executes a new move model command.
    /// \paramp[in] _modelName Scoped name of model which was moved.
    /// \param[in] _startPose Start pose
    /// \param[in] _endPose End pose
    private: void UserCmdManager::NewMoveModelCmd(std::string _modelName,
        ignition::math::Pose3d _startPose,
        ignition::math::Pose3d _endPose)
    {
      MoveModelCmd cmd = new MoveModelCmd(_modelName, _startPose, _endPose);

      // Add it to undo list
      this->userUndoCmds.push_back(cmd);

      // Clear redo list
      this->userRedoCmds.clear();
    };

And when the user presses undo:

    /// \brief Callback when an undo request is received.
    private: void UserCmdManager::OnUndo()
    {
      // Get the command
      UserCmd *cmd = this->userRedoCmds.back();

      // Undo it
      cmd->Undo();

      // Remove from undo list
      this->userUndoCmds.pop_back();

      // Disable undo action if there are no more commands in the list
      if (this->userUndoCmds.empty())
        this->DisableUndo();

      // Add command to redo list
      this->userRedoCmds.push_back(cmd);
    };





