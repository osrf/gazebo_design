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

The architectural diagram below illustrates the clock noise architecture. Two clocks are attached to different (or the same) model links. As part of their definition these clocks implement a single noise model, the goal of which is to perturb global time. Each of the three sensors specifies which noise stream is used to time stamp measurements produced by the sensor.

![Clock noise architecture](https://bytebucket.org/asymingt/gazebo_design/raw/64c4864a193551098cd0fb4e7ae1edc4269c7608/improve_sensors/clocknoise.png "Clock noise architecture")

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

The performance of time stamping sensor measurements will now depend on the run-time complexity of the noise model. It may perhaps be prudent to write a test case for profiling the execution time of the various noise models to ensure that performance is maintained.

### Tests

1. Test: Clock noise model
    1. case: Create a single Guassian clock noise model and test that IMU sensor time is perturbed correctly.
    1. case: Create a sensor with no clock model specified and test that IMU sensor time is equal to global time.
1. Test: Clock noise performance
    1. case: Generate IMU measurements at 1000kHz for Gaussian noise type 

### Pull Requests

None yet.