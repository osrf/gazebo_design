## Project: Add clock noise to sensor measurement timestamps
***Gazebo Design Document***

### Overview

Gazebo sensors currently time stamp their measurements with global time. 
However, in reality, as a result of imperfect clocks time stamps often differ 
across platforms -- even when a clock disciplining method like NTP is used. 
The underlying reason for this error is that clocks are driven by an oscillator 
that suffers random noise, as well as temperature and age related error.

There is a well adopted model for clock error, which is used to model drift (dt)
between the satellite vehicle clock and a perfect clock on the

  dt = a0 + a1 (t - t0) + a2 (t - t0)^2 + k

The a0 term is called the bias, while a1 is the drift. The a2 term is the rate
of drift of the clock with respect to a reference time base. The time t0 is a
reference epoch, and t is the current reference time. k is random noise.

### Requirements

1. Each model should be able to define an arbitrary number of clocks, each 
   having a unique identifier
2. Each clock drifts acording to a standard model, with a noise model term
3. Each sensor can specify a clock to use when time stamping measurements
4. By default (clock unspecified) the time stamps are perfect (global time)

### Architecture

The architectural diagram below illustrates the clock noise architecture. Two 
clocks are attached to different (or the same) model links. As part of their 
definition these clocks implement a single noise model, the goal of which is 
to perturb global time. Each of the three sensors specifies which noise stream 
is used to time stamp measurements produced by the sensor.

![Clock noise architecture](https://bytebucket.org/asymingt/gazebo_design/raw/64c4864a193551098cd0fb4e7ae1edc4269c7608/improve_sensors/clocknoise.png "Clock noise architecture")

### Interfaces

#### SDF changes ####

Addition of ```clock.sdf```

```
<element name="clock" required="0">
  <description>These elements define a unique clock source</description>
  <element name="id" type="string" default="default" required="1"/>
  <element name="bias" type="double" default="0.0" required="1"/>
  <element name="drift" type="double" default="0.0" required="1"/>
  <element name="rate" type="double" default="0.0" required="1"/>
  <element name="reference" type="double" default="0.0" required="1"/>
  <include filename="noise.sdf" required="0"/>
</element>
```

Changes to ```link.sdf```

```
<element name="link" required="+">

  ...

  <include filename="clock.sdf" required="*"/>

</element>

```

Changes to ```sensor.sdf```

```
<element name="sensor" required="0">

  ...

  <element name="clock" type="string" default="none" required="1"/>

  ...

</element>
```
#### API changes ####

Sensors currently generate time stamps by obtaining a pointer to the world at 
load time and then accessing the ```World::GetSimTime()``` when time is needed: 

A sensor will typically time stamp its measurement in the following way:

```
msgs::Set(msg.mutable_time(), this->scene->GetSimTime());
```

We want to effectively insert a proxy function that noise-perturbs time.

To do this we'll added some initialization code to ```Link::Load``` which sets
up a clock noise model for the sensor. A ```Sensor::GetClockTime``` method acts
as a proxy through which sensors access time. This method will add on a small
component of error that represents the difference between the local clock and
the global time obtained from ```World::GetSimTime()```.

For example in ```Link.hh``` we'd define a map of clock noise models

```
class GZ_PHYSICS_VISIBLE Link : public Entity
{
  protected: std::map<std::string,sensors::SensorNoiseType> clocks;
} 

```

And in ```Link.cc``` we'd populate this list

```
void Link::Load(sdf::ElementPtr _sdf)
{
  if (_sdf->HasElement("clock"))
  {
    sdf::ElementPtr clockElem =_sdf->GetElement("clock");
    while (clockElem)
    {
      this->clocks[clockElem->Get<std::string>("name")] =
        NoiseFactory::NewNoiseModel(
          clockElem->GetElement("noise"));
    }
  }

```

Then, we'd implement the ```Sensor::GetClockTime``` proxy function...

```
common::Time Sensor::GetClockTime(const common::Time &in)
{
    return this->parentLink->clocks[this->GetClock()].Apply(in);
}

```

One thing to think about at this point is whether SensorNoiseType actually 
belongs inside the ```sensor``` namespace and not the ```math``` namespace...

### Performance Considerations

The performance of time stamping sensor measurements will now depend on the 
run-time complexity of the noise model. It may perhaps be prudent to write 
a test case for profiling the execution time of the various noise models to 
ensure that performance is maintained.

### Tests

1. Test: Clock noise model
    1. case: Create a single Guassian clock noise model and test that IMU 
       sensor time is perturbed correctly.
    1. case: Create a sensor with no clock model specified and test that 
       IMU sensor time is equal to global time.
1. Test: Clock noise performance
    1. case: Generate IMU measurements at 1000kHz for Gaussian noise type 

### Pull Requests

None yet.