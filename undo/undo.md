# Undo / Redo user commands during simulation

## Overview

Users often wish to undo commands while editing their worlds in simulation. For
example, a user moves a robot from one place to another in the world and then
they want to revert that command so the robot goes back to its previous
position.

The expected undo behaviour in a simple case like the one above is quite clear.
However, worlds in Gazebo are not only affected by user commands, but also by
the physics engine and plugins. Moreover, several clients might be connected to the same
simulation and be editing it at the same time. When all of these are happening at
the same time, it might not be so clear what is expected from the undo command.

Let's look at a more complex example. We have a vehicle being controlled by
a plugin to drive between several cones. the user moves the vehicle to the
beginning of the course and then the plugin starts controlling it.



