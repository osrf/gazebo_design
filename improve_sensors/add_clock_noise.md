## Project: Bring the IMU sensor inline with the generic noise model architecture
***Gazebo Design Document***

### Overview

Gazebo sensors currently time stamp their measurements with global time. However, in reality, as a result of imperfect clocks
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

#### SDF changes ####

Addition of ```clock.sdf```

```
<element name="clock" required="0">
  <description>These elements define a clock source</description>
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

  <clock name="name" type="string" default="none" required="1">
    <description>A reference to the clock used to time stamp sensor measurements.</description>
  </clock>

  ...

</element>
```
#### API changes ####

Sensors currentl generate time stamps by obtaining a pointer to the world at load
time and then accessing the ```World::GetSimTime()``` when time is needed: 

For example, ```GpsPlugin``` time stamps in this way:

```
this->lastMeasurementTime = this->world->GetSimTime();
```

While, the ```CameraSensor``` time stamps in this way:

```
msgs::Set(msg.mutable_time(), this->scene->GetSimTime());
```

Having discrete events generated according a custom time basis will significantly 
complicate the simulation core. So, we'll just assume that the sensor is triggered
along the global time axis. The only difference is that, with a noisy clock,
the time stamps associated with each measurement are noise corrupted.

To do this we'll added some initialization code to ```Link::Load``` which sets
up a clock noise model for the sensor. We'll implement ```Sensor::GetClockTime``` 
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


One thing to think about at this point is whether SensorNoiseType actually belongs
inside the ```sensor``` namespace and not the ```math``` namespace...


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