# Simulation Validation Tool for Gazebo

## Overview

The simulation validation tool enables users to statistically compare data
gathered from a real robot to sensor and actuator information computed in
Gazebo. It strives to answer a question asked by many Gazebo users:
"how well does this simulated robot model reflect reality?"

## Requirements

Inputs:

* A robot model (SDF or URDF) with physically accurate inertial properties
* A time series of commanded joint states
* A time series of sensor data (force/torque sensors, encoder data, etc.)

Output:
* The robot carries out the commanded joint state trajectory in simulation.
* Simulated sensor data of the same type is recorded.
* A diff of the sensor data is computed
* Statistics are computed: RMSE, max error, min error, etc.

### Additional features

The following are features that are unnecessary for the minimum viable
implementation of this tool, but would greatly enhance its usability.
Some of these features are discussed in this design document.

* GUI panel for selecting an input data file, displaying output, selecting an output file
* Plotting UI for visually comparing real world data to simulation data
* UI for tuning robot model parameters
  * Allow parameter tuning in-the-loop and recomputing of statistical data
* UI for tuning simulation parameters such as step size, friction on world objects, etc.
  * Allow parameter tuning in-the-loop and recomputing of statistical data
* "Real-time" data collection and statistics computation (requires real-time factor less than 1)
* Support variable sampling rate
* ROS integration
  * This may end up being a primary feature, since it could simplify the interfaces
* Better sensor and motor interfaces
  * The ability to increase simulation accuracy increases the utility of this tool
* Better world state saving/loading interfaces
  * To ensure matching initial conditions in simulation and reality

## Architecture

((todo: flowchart))

### SignalInterface class

The `SignalInterface` class is a minimal interface between a source of real-world
data, a source of simulation data, and the `SignalStats` class, which
accumulates statistics based on the collected signals.

There is one `SignalInterface` per robot property (joint command or sensor value).
`SignalInterface` is templated on the type of the property (e.g. `double`,
`Vector3`).

#### Sources of real-world data

`SignalInterface` keeps a time-ordered buffer of real-world data points as they
arrive (whether from a file, a ROS topic, or a Gazebo/`ign-transport` topic).
This buffer is referred to as the "input buffer".

The data point is identified by a key, which is the name of its column if the
data is read from a file, or the name of the topic that it came in on.

Data point keys are scoped as follows:

`<name of SDF joint or sensor element>/property/property key`

An example scoped key to specify the x-component of wrist joint's linear velocity
in a data file might be:

`wrist_0/linear_vel/x`

When `SignalInterface::ProcessInputBuffer` is called, data points in the input
buffer are matched with data points in the output (simulation) buffer with the
same key and the same timestamp, and calculations are performed.
Data points with no match are left in the buffer.

#### Sources of simulation data

`SignalInterface` keeps a time-ordered buffer of simulation data points, the "output buffer".

How does the system match the key for an input data point to the source of
its corresponding output, i.e. the Gazebo function returning the correct value?

If the robot `Model` is stored in the class, a simple traversal of the `Base` class
could be written to find the child element that matches the first component of the scoped key.
However, a lot of boilerplate code may be needed to match the joint/sensor property
key to the corresponding function in `Joint`/`Sensor`.

Once the matching function is found, it could be stored generically in the `SignalInterface`
class using a function pointer or a lambda that wraps the result in a data point and
pushes it to the buffer.

### SampleScheduler class

The `SampleScheduler` class instantiates and manages `SignalInterface` objects
based on the parsed input.
It also schedules the adding of and consuming data from the input
and output buffers based on the input method and the timing needs of the data.

### Timing

The input signal from the real world sets the sampling rate of data in simulation.
To deliver accurate statistics, the sample interval between two points in simulation
must exactly match the interval between their corresponding input points.

To simplify timing logic, the system only considers input points with a monotonically
increasing timestamp. If it encounters a point with an earlier timestamp than the
latest time it as seen, it discards the point. If it encounters a duplicate timestamp
(equal to the latest time it has seen), it discards the corresponding point.

Simulation time must be measured at an offset from the initial input sample point.
This is easily accomplished if the relative time between sample points is considered,
not the absolute time.

How does the system determine when to sample simulation data points and add them
to the output buffer?

If the sampling rate of input points is constant, the answer to this question is
trivial: the system runs the simulation as usual and samples data at the requested
sampling rate.

If the sampling rate is not constant, the system must buffer a window of input points,
analyze the timing differences between points in the buffer based on the intervals
between input points, and schedule samples at those times.

When scheduling simulation samples, the granularity of simulation timesteps must
be considered, as well as the synchronization of periodic samples. If the minimum
step size in simulation is much larger than the minimum step size in the input
signal, it will be impossible to find a simulation sample for each point in the
input signal.

There should also be a tolerance parameter that controls the biggest difference
between the timestamp of an input and an output point for them to be matched.

### Threading Model

When `SampleScheduler` schedules a simulation sample, the function that retrieves
the data point must occur after the world update loop. To that end, `SampleScheduler`
will queue those functions using a `lambda` or a similar function 

## Interface

Steps for the user on a typical run of the tool

### Input data file format

### GUI

### ROS interface

## Performance Considerations

If this tool is 

## Tests

### Unit Tests

### Validation test cases

#### Uncontrolled system

#### Controlled system

### User Studies

Because this tool is meant to be used by robotics researchers, it may be fruitful
to run user studies with research groups using the completed minimum viable version
of this tool. This will direct the evolution of the tool in the large space of possibilities
enumerated in the "additional features" section.

## Pull requests
