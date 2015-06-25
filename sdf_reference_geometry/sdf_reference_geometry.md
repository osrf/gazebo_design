## Project: SDF reference geometry
***SDF Design Document***

### Overview

Inspired by Solid Work's reference geometry tools, the Idea is to have the ability to define frames of references in SDF and reference them using an extended version of the pose elements.


### Requirements

1. Be able to define reference geometries inside the following elements: link, joint.
1. Provide a type to help with visualization (axis, or frame)
1. Be able to reference that geometry, using the path of the frame element.

### Example

In this example, robot Robo is defined in sdf, using frames to define relative poses.

![kinematic chain](links.png)


~~~

<sdf version='1.x'>
  <model name="Robo">

    We define a frame named mframe, relative to the world frame
    The world frame always exists, but other frames need to be defined.
    The mf1 frame has an offset of x=1 and y=1 with respect to the world frame

    <frame name="mframe">
      <pose frame='world'>1 1 0 0 0 0</pose>
    </frame>

~~~

As before, our model "Robo" needs a pose. The pose element has a new attribute, frame.
This pose is relative to the "mf1" frame (x=1) and therefore the pose evaluates to x=2 y=1 in the world frame.

~~~
    <pose frame="mf1">1 0 0 0 0 0</pose>


      <link name="l1">
      <frame name="l1frame">
        <pose frame="mframe">0 0 0 0 0 0</pose>
      </frame>
      <pose frame="l1frame">0 0 0 0 0 0</pose>
    </link>

    <joint name="j1">
      <frame name="j1frame">
        <pose frame="l1">
      </frame>
    </joint>

    <link name="l2">
      <frame name="l2frame">
        <pose frame="mframe">0 0 0 0 0 0</pose>
      </frame>
      <pose frame="l1frame">0 0 0 0 0 0</pose>
    </link>


    </>

~~~


In this example, a frame named axis0 is defined in the model's torso link. It has a type element, for UI purposes. The convention is to use the Z axis. The axis1 frame is defined as an offset of axis0

<sdf version="1.5x">
  <model name="Robo">

    <link name="l1">
      <frame name="axis0">
         <pose>1 0 0 0 0 0</pose>
         <type>axis</type>
      </frame>
      <frame name="axis1">
         <pose frame="axis0">0 -1 0 0 0 0</pose>
      </frame>
    ...</>

This is how thew frame can be used elswhere in the sdf files, using its path name: "Robo::torso::axis0"


<sdf version="1.5x">
  <model name="Robo">
    ...
    <link name="arm0">
      <pose frame="Robo::torso::axis0">1 0 0 0 0 0</pose>

     ...</>


In this example, we use a collision and a visual as frames. Anything that has a unique pose can be used as a frame, but elements (links, models, ...) can define multiple frames.


<example missing>



In a world file, frames can be used across models.


<world>
  <frame "center">
  <frame "offense">
  <frame "defense" >


  <model name="Robo"></>

  <model name="Robo2">
    <pose frame='Robo::torso'>0 0 0.01 0 0 0</pose>
  </>


### Challenges

1. The proposed changes makes it more difficult for SDF parsers, because a pose may be defined by a succession of multiple frames. Using the SDF library will shield the user from this added complexity, because it should provide the element lookups to perform this task.
1. Because pose elements are estimated relative to other frame elements, this design introduces the possibility of a circular dependencies.

### Open questions, limitations

1. Should it be possible to define frames in a world file? This could be useful for models defined in the world file, but could prevent a model to be used in any world, unless a default pose is assumed.

### Architecture

Evaluation of a pose is now done recursively. Appropriate action must be taken when frames are not found, or circular dependencies are detected.


### Interfaces

1. frame element: This is a new XML SDF element
1. pose element: the frame XML attribute is added to the pose element.

For example:
Plot proto message: A message that carries plot data will be created to transmit data from the server to the client.

Include any UX design drawings.

### Performance Considerations

This design should not impact perfromance much. While there is an added cost to compute each pose element, this cost can be done once when the sdf is loaded.

### Tests
List and describe the tests that will be created. For example:

1. Test: built in reference frames:
    1. case: the world frame, using joint as frames
    1. case: frame elements defined in model, link, (collision? visual?)
    1. case: on circular references, their detection and error messages.
1. Test: Multiple plots
    1. case: Create two plots with identical data. Saved CSV data from each should be identical

### Pull Requests


The pull requests that will be created to merge this project are:

1.




