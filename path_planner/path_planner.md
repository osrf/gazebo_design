# Path Planner Library for Gazebo #
***Gazebo Design Document***

## Overview ##

Gazebo does not currently have any plugins for point-to-point model movement.
The goal of this project is to create a plugin for model movement that uses an
external path-planning library to navigate a model to a target location while
avoiding collision with obstacles within the world. Implementing this plugin
will allow Gazebo users to program more sophisticated model simulations with
greater ease and less code.

Currently, the plan is to design this path planner plugin with interfaces to 
several path planning options of various complexity. First, the plugin should
include a very simple path planner would could be incorporated entirely within
Gazebo. More complex, more customizable options include 
[The Open Motion Planning Library](ompl.kavrakilab.org),
which seems like a good candidate, thanks to its conprehensive libraries, and extensibility.

Similarly, the plugin should offer users different movement options for their 
models. We plan to a range of options from simple 'pushing' (in which the model 
disappears and reappears at point along the path with rough granularity, to 
more complex movement schemes that may be specified by the user.

This plugin is intended to first offer basic functionality, initially handling 
only basic movement options and 2D path planning, but will be extended over time
to allow for more complex planning and customization.


## Requirements ##

The main requirements of this project are to create an path planner plugin 
which will use take input start and end positions from the user, configure input
and compute a valid path, then use this output to move the model along
the specified path. These computations will require the creation of a cost map 
which will translate the collision objects and details of the world into a 
format suitable for use within the path planning algorithm.

Since this plugin is designed with the intent of offering multiple planner 
and movement interfaces, the plugin must be able to manipulate 
data into formats viable for use in any of these interfaces.

OMPL itself has a few requirements, as discussed 
[here](http://ompl.kavrakilab.org/geometricPlanningSE3.html). 
It requires that the user specify the state space to planning it, define bounds
for the space, define the notion of state validity, and finally, define the start
state and goal state. The most substantial of these goals will be defining state
validity, which will involve interpreting world information to determine where 
obstacles, invalid path states, will be. Details on state validity are outlined 
[here](http://ompl.kavrakilab.org/stateValidation.html).
This information should be embedded in the cost map.

## Architecture ## 

### Plugin ###

Input Parameters

1. A goal position for the model.
1. An array containing starting position and zero or more intermediate points.
1. A choice of path planner interface.
1. A choice of movement interface.

Once we implement the OMPL or any complex planner interfaces, the plugin may
require more input parameters. For example, OMPL offers many optimization
options that users should eventually be able to choose between.

Before instantiating the path planner class, the plugin will generate a cost
map. Our current approach will build off the ray tracing method detailed
[here](http://gazebosim.org/tutorials?tut=custom_messages#CollisionMapCreatorPlugin),
which rasterizes 3D world information, then uses 
[ray intersection](https://bitbucket.org/osrf/gazebo/src/f41484ce1fe3451075a61311d4b7e14c086a5f4e/gazebo/physics/RayShape.cc?at=default)
to generate a 2D collision map.

After instantiating a path planner interface, passing the cost map and other
required parameters, the plugin receives the calculated path from the planner
and formats it for use in a movement interface, which generates the necessary
movement messages.

Output: Using the correct movement interface, the model should move along a 
collision free path to the goal position, passing through any specified 
intermediate points.

### Path Planner Interfaces ###

This section will be updated as more path planners are supported.

#### Simple Planner Interface ####

The simple planner will be a basic path planning algorithm embedded within 
Gazebo code. The interface will depend on the implementation of this planner
class, which is yet to be determined.

#### OMPL Interface ####

The plugin should instantiate a class responsible for configuring and calling
OMPL, call it ompl_interface. ompl_interface should receive start position,
goal position, and space information via the world pointer. ompl_interface
should then:

1. Construct the state space (should always be 3d space for Gazebo).
1. Set the space bounds according to the world pointer. 
1. Create an instance of ompl::geometric::SimpleSetup.
1. Set a state-validity checker.
1. Set start and goal states. 
1. Run a planner.
1. Return the path, a 1xN matrix of states. 

OMPL will also require a state-validity checker, a boolean function which
declares whether a given state, or model position, is valid for a model. An
invalid state will be any state in which the model collides with another object
within the world. In order to check for collisions, the class must read the
list of existing objects from the world pointer, then ensure that the model
does not intersect with any of them.

### Movement Interfaces ###

This section will be updated as more movement interfaces are supported.

#### Push Interface ####

This will move a model by pushing it from point to point along the path
calculated by the planner. This will involve sending a movement message for
each of the points specified by path. The granularity of this movment may
be made adjustable via plugin parameter.

## Interfaces ##

The parameters to the path planner plugin will be specified via sdf. As discussed,
the plugin will operate with a specified path planner interface and movement
interface. The plugin will first calculate a cost map based on the obstacles 
in the world, then pass this information along to the specified path planner
interface, where it will be reconfigure if necessary. After path calculation,
the plugin will format the path output and pass it along to a specified movement
interface, which will generate the appropriate movement directions and pass
them to the server (see open questions).

## Performance Considerations ##

This project's performance considerations are unclear, as the costliness of the
path planner will vary by simulation. Because OMPL offers algorithm and
optimization technique customization options, users should eventually be able
to tune these options to suit their usage of the plugin.

## Tests ##

This plugin will use an integration test. Each of the path planner interfaces
and movement interfaces will need to be tested individually. We will provide a 
number of test input parameters for each interface, then check that the output 
path positions are as expected, and that movement messages are being passed 
correctly.

## Open Questions & Confusion ##

1. Given the matrix of states that OMPL returns, how do we transform those
   states into movement messages?