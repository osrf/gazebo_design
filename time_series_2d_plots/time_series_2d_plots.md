## Project: Time series 2d data plots
***SDF Design Document***

### Overview

Gazebo simulations can generate a lot of useful data. It would be useful to be
 able to see some of that data in real time on 2d plots. This can be done in
 C++ and QT inside Gazebo, or as a separate application using GazeboJs.

### Requirements

1. Be able to identify useful numerical data source and make them available
 for plotting.
1. Be able to configure plots (min, max, colors, sampling rate, data buffer size).
1. Be able to save the plot and or the data
1. (Nice to have) Be able to specify derived values (like combining
 X, Y ,Z positions to plot a distance).

### User Interaction

Here is a high level design of what this tool could look like. It is written
 for an implementation inside Gazebo, but the UI can also apply to an external
 application.

[plotting v3](https://bitbucket.org/osrf/gazebo_design/raw/db9782356501878b0df60b396f9d54860cc7d28c/time_series_2d_plots/Plotting_v3.pdf)


### Plottable Data

In a simulation, the physics server generates large volumes of data over time.
Here is a list of physics data that should be made available to the plotting
tool.

**Topics**
Only numerical fields in messages can be plotted

**Model**

  - pose

  - **Link**
    - pose
    - angular acceleration
    - anular velocity
    - linear acceleration
    - linear veloicty
    - force
    - torque

    - **Collision**
        - pose

    - **Visual**
        - pose

  - **Joint**
    - pose
    - force
    - torque

  - **Model**
    - ...

**Simulation**

  - sim time

  - wall time

  - iterations

  - real time factor

The three different categories of data shown above correspond to the those in
the left panel of the plotting tool as shown in the
[plotting v3](https://bitbucket.org/osrf/gazebo_design/raw/db9782356501878b0df60b396f9d54860cc7d28c/time_series_2d_plots/Plotting_v3.pdf)
design document.

### Implementation

**Topics**

The plotting tool will subscribe to Gazebo topics upon user selection from
a Gazebo topic list similar to the Topic Viewers. It needs to be able to
identify the message type for that topic and list the fields that can be
plotted. Protobuf message reflection can help to retrieve the names and
data types for the fields in the message.

Here is an example showing the plottable fields for the message type
`gazebo.msgs.PosesStamped` published to the `~/pose/local/info` topic:

~~~
gazebo.msgs.PosesStamped
  + time
  + pose
~~~

Expanding the `time` field will reveal more fields:

~~~
gazebo.msgs.PosesStamped
  - time
      - sec
      - nsec
  + pose
~~~

Since `pose` is a repeated field in the `gazebo.msgs.PosesStamped` message,
expanding the pose field will show an list of indices which correspond to the
indices in the pose array.

~~~
gazebo.msgs.PosesStamped
  + time
  - pose
      - [0] [1] [2] [3] [4] [5]
      - name
      - id
      - position
        - x
        - y
        - z
      - orientation
        - x
        - y
        - z
        - w
~~~

Clicking on an index number within the [] bracket will highlight it and expose
the fields of the `gazebo.msgs.Pose` message. The `name` field could be
filled with its string value while the numerical fields could be dragged
over to the plotting area to begin the plot.

**Model**

Not all data generated by the physics server are currently available to the
client, such as link velocity and acceleration. Neither are these data
published to topics nor accessible using the Gazebo request-response mechanism.


The physics World class has a convenient function to collect physics data of
entities using the `WorldState` data structure, e.g.

~~~
  WorldState worldState(worldPtr);
  worldState.FillSDF(stateElem);
~~~

We then need to convert the state SDF element `stateElem` into a protobuf
message by implementing a `msgs::StateFromSDF` function in msgs.cc so that it
can be published over a custom Gazebo topic for the plotting tool, e.g.

topic:

~~~
~/plotting/world_states
~~~

message structure:

~~~
gazebo.msgs.JointState
  required string name
  optional unit32 id
  optional Pose pose
  optional Pose angle

gazebo.msgs.CollisionState
  required string name
  optional unit32 id
  optional Pose pose

gazebo.msgs.VisualState
  required string name
  optional unit32 id
  optional Pose pose

gazebo.msgs.LinkState
  required string name
  optional unit32 id
  optional Pose pose
  optional Pose velocity
  optional Pose acceleration
  optional Wrench wrench
  repeated visual
  repeated collision

gazebo.msgs.ModelState
  required string name
  optional unit32 id
  optional Pose pose
  repeated link
  repeated model
  repeated joint

gazebo.msgs.WorldState
  repeated model
~~~

One performance improvement is to provide the `WorldState` class a feature
to selectively populate only data required by the plotting tool. For example,
if the user chooses to plot the linear z acceleration of the
`box::link_0` entity. The `WorldState` will apply a filter while traversing
over the tree of entities to retrieve only the requested data for the specified
entity.

The set this filter, the client can publish a message over another custom
Gazebo topic, e.g.

topic:

~~~
~/plotting/world_state_filter
~~~

The filter message can potentially be the `gazebo.msgs.WorldState` message where
the filter is built by initializing an optional field in the message with a
non-zero value. Alternatively, a different message made up of similar fields
but `bool` data types can be used for performance improvement.

**Model**

Simulation data are available via the  `~/world_stats` topic.


### Notes about GazeboJs

There are multiple graph libraries for JavaScript (d3, flot, sigmajs ...) that
 can be used to make a graph utility for Gazebo. The graphing feature can than
 be added to GZweb, and also packaged as a stand alone application with a
 toolkit like [electron](https://github.com/atom/electron).

GazeboJs cannot access new types of messages that are created by Plugins.