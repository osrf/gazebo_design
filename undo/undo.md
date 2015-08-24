# Undo / Redo user commands during simulation

## Overview

Users often wish to undo commands while editing their worlds in simulation. For
example, a user moves a robot from one place to another in the world and then
they want to revert that command so the robot goes back to its previous
position.

![Simple case](https://bytebucket.org/osrf/gazebo_design/raw/341d26c17ada15ec67f46048fd30a404c47a46f4/undo/simple_case.png)

The expected undo behaviour in a simple case like the one above is quite clear.
However, worlds in Gazebo are not only affected by user commands, but also by
the physics engine and plugins. Moreover, several clients might be connected to the same
simulation and be editing it at the same time. When all of these are happening at
the same time, it might not be so clear what is expected from the undo command.

Let's look at a more complex example. We have a vehicle being controlled by a
plugin to drive between several cones.

1. The user moves the vehicle to the beginning of the course.

1. Then the plugin starts controlling it.

1. The vehicle hits a cone and it falls.

If the user hits undo now, what should it do?

![Plugins plus physics](https://bytebucket.org/osrf/gazebo_design/raw/341d26c17ada15ec67f46048fd30a404c47a46f4/undo/cmd_plugin_physics.png)

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

* Physics / plugin effects which resulted from a user command are undone when
the user command is undone.







