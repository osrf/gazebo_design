## Project: Helper Classes for Computing Signal Statistics
***Gazebo Design Document***

### Overview

This design document is motivated by physics accuracy testing for Gazebo.
Physics accuracy tests generate discrete samples of time-varying error signals (see Figure 1),
such as deviation of measured position or velocity from a desired trajectory.
To simplify comparson of these signals,
scalar statistical properties (or metrics) can be computed
from the vector of discrete error samples,
for example, maximum error or root mean-squared error.
This document outlines helper functions for computing these properties.

![Discrete samples of a time-varying signal](https://bitbucket.org/osrf/gazebo_design/raw/69d0c56c8ae18f79cdabcc40a9cedf13e51b480e/signal_stats/discrete_signal.png)
Figure 1: Discrete samples of a time-varying signal.

### Requirements

The target use case is a loop that inserts data many times and reads data once at the end of the loop.
Additionally, real-time performance is being measured based on the time elapsed during the loop.
See the following pseudo-code as an example:

~~~
startTime = getWallTime();
for many steps:
  data = generateData()
  statistic.InsertData(data)
end
elapsedTime = getWallTime() - startTime
output = statistic.Get()
~~~

In order to accurately measure real-time performance,
the InsertData function should have minimal performance impact.
Storing an entire data sequence is not feasible due to
the performance impact of dynamic memory allocation and/or
writing data to a disk.
Instead, statistics will be computed incrementally.
This is easy for certain statistics (mean, max)
but hard or impossible for others (median).

Additionally, a minimal amount of code should be required
to compute these statistics.
Helper functions will be provided that allow computation of
multiple statistics per signal
(i.e. mean, max, root mean-square, etc.)
as well as helper functions for math::Vector3 types.

### Architecture
Create a hierarchy of classes starting from the bottom:

* class SignalStatistic: Generic class for computing statistics on a discrete-time signal.
The statistics should be computed incrementally for each new data point without
storing the entire time history of the signal.
The class should be overloaded to implement the specific statistics (mean, max, root mean-square).
* class SignalStats: Contains multiple SignalStatistic objects and provides an
interface to pass a single sample to each statistic.
Should also return the value of each statistic
in a map keyed by name ("Max", "Mean", "Rms").
* class Vector3Stats: Similar to SignalStats but takes a Vector3 instead of a scalar.
It should compute separate statistics on the scalar components x, y, z,
and the vector magnitude (see Figure 2).

![Signal statistics hierarchy](https://bitbucket.org/osrf/gazebo_design/raw/69d0c56c8ae18f79cdabcc40a9cedf13e51b480e/signal_stats/signal_stats_hierarchy.png)
Figure 2: Signal statistics hierarchy for Vector3Stats.

### Interfaces
SignalStatistic class, use InsertData(double) to add data,
Get() to get the current value of the statistic,
and GetShortName() to get a label for the statistic (used by GetMap in SignalStats).
Those are pure virtual, so they should be implemented by derived statistic classes.
The data and count variables are used to store the current value of the statistic.
Implement 3 derived classes:

* SignalMean
* SignalRootMeanSquare
* SignalMaxAbsoluteValue
~~~
class SignalStatistic
{
  public: void InsertData(double _data) = 0;
  public: double Get() = 0;
  public: std::string GetShortName() = 0;
  private: double data;
  private: unsigned int count;
};
~~~

SignalStats class, use InsertStatistic to add statistic to a signal,
InsertData to add a data point, and GetMap to get the current values.
Contains a vector of SignalStatistic objects.
~~~
class SignalStats
{
  public: bool InsertStatistic(const std::string &_name);
  public: void InsertData(double _data);
  public: std::map<std::string, double> GetMap();
  private: std::vector<SignalStatistic> stats;
};
~~~

Vector3Stats class: contains 4 SignalStats objects (xyz and magnitude),
use InsertStatistic to add a stat to each scalar component,
use InsertData(Vector3) to update all 4 signals with a single function call.
~~~
class Vector3Stats
{
  public: bool InsertStatistic(const std::string &_name);
  public: void InsertData(const math::Vector3 &_data);
  public: SignalStats x;
  public: SignalStats y;
  public: SignalStats z;
  public: SignalStats mag;
};
~~~

### Performance Considerations
Don't store complete time history of signals.
Compute statistics incrementally to reduce memory requirements.
This is easy for certain statistics (mean, max)
but hard or impossible for others (median).

It is anticipated that inserting data points will happen more often
than getting the statistical values.

### Tests

1. SignalStatistic Unit Test:
    1. Constructor: without inserting data, expect Get() == 0
    1. Insert multiple constant values.
    1. Insert constant magnitude with alternating sign.
1. SignalStats Unit Test:
    1. Add mean and rms statistics. Insert multiple constant values.
    1. Add mean and rms statistics. Insert constant magnitude with alternating sign.
1. Vector3Stats Unit Test:
    1. Add mean and rms statistics. Insert Vector3::UnitX, Vector3::UnitY.

### Pull Requests
This design was implemented in
[gazebo pull request 1198](https://bitbucket.org/osrf/gazebo/pull-request/1198/new-math-class-signalstats/diff),
though some changes to the API were made in response to the pull request comments.
It modified the `INTEGRATION_physics_inertia_ratio` test to use
these classes.

The design was added to ignition-math in the following pull requests:

* https://bitbucket.org/ignitionrobotics/ign-math/pull-requests/34
* https://bitbucket.org/ignitionrobotics/ign-math/pull-requests/42
* https://bitbucket.org/ignitionrobotics/ign-math/pull-requests/45
