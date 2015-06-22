## Project: Timestamp sensor measurements using common noise-corrupted clocks 
***Gazebo Design Document***

### Overview

Gazebo sensors currently time stamp their measurements with global time. However, in reality, as aresult of imperfect clocks
time stamps often differ across platforms -- even when a clock disciplining method like NTP is used. The underlying reason for 
this error is that clocks are driven by an oscillator that suffers random noise, as well as temperature and age related error.

### Requirements

1. Each model should be able to define an arbitrary number of clocks, each having a unique identifier
2. Each clock defines a noise model, which perturbs the current global time
3. Each sensor can specify a clock to use when time stamping measurements
4. By default (clock unspecified) the time stamps used are perfect (global time)

### Architecture
Include a system architecture diagram.
This should be a conceptual diagram that describes what components of Gazebo will be utilized or changed, the flow of information, new classes, etc.

### Interfaces

Addi

Changes to ```sensor.sdf```

```
<element name="sensor" required="0">

  ...

  <clock name="name" type="string" default="none" required="1">
    <description>A reference to the clock used to time stamp sensor measurements.</description>
  </clock>

  ...

</element>
```

### Performance Considerations
Will this project cause changes to performance?
If so, describe how.
One or more performance tests may be required.

### Tests
List and describe the tests that will be created. For example:

1. Test: Plot View
    1. case: Plot window should appear when signaled by QT.
    1. case: Plot simulation time should produce correct results when save to CSV
    1. case: Signalling a close should close the plotting window.
1. Test: Multiple plots
    1. case: Create two plots with identical data. Saved CSV data from each should be identical

### Pull Requests
List and describe the pull requests that will be created to merge this project.
Consider separating large refactoring operations from additions of new code.
For example, the physics::SurfaceParams class was refactored in
[pull request #891](https://bitbucket.org/osrf/gazebo/pull-request/891/refactor)
so that a new FrictionPyramid class could be added in
[pull request #935](https://bitbucket.org/osrf/gazebo/pull-request/935/create).

Keep in mind that smaller, atomic pull requests are easier to review.