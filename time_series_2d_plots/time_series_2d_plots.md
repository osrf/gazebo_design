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

### Gazebo transport

The Gazebo transport library allows the gzclient to interact with the
 simulation server gzserver. This interaction is done via streams of messages
 called topics. Messages contain numerical values (and sometimes time stamps) that
 can be plotted. Plugins can also create new message types and topics.

In Gazebo 6 and 7, the transport library is in the Gazebo source tree. Gazebo 8
 will switch to the [ign-transport](https://bitbucket.org/ignitionrobotics/ign-transport).
 This project targets the currently used transport library in Gazebo and GazeboJS.
 In Gazebo 7, both transports are available, but ign-transport does not carry the data
 used for plotting.

For example, the plotting system could subscribe to the `~/pose/info` topic to get
 entity pose data over time.

### Notes about GazeboJs

There are multiple graph libraries for JavaScript (d3, flot, sigmajs ...) that
 can be used to make a graph utility for Gazebo. The graphing feature can than
 be added to GZweb, and also packaged as a stand alone application with a
 toolkit like [electron](https://github.com/atom/electron).

GazeboJs cannot access new types of messages that are created by Plugins.
