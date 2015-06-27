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

![kinematic chain](links.png =320x)


~~~

<sdf version='1.x'>
  <model name="Robo">
~~~

We define a frame named mframe, relative to the world frame
The world frame always exists, but other frames need to be defined.
The model frame "mmframe" has an offset of x=1 and y=1 with respect to the world frame.
Like in previous versions of SDF, our model "Robo" has a pose. The pose element has a new attribute, frame, which makes
this pose relative to the "mframe" frame. Therefore the final pose evaluates to x=2 y=1 in the world frame.

~~~
    <frame name="mframe">
      <pose frame='world'>1 1 0 0 0 0</pose>
    </frame>
    <pose frame="mframe">1 0 0 0 0 0</pose>
~~~

Link 1 also defines frames:

1. A baseframe "l1frame" relative to mframe. This is the framed used to express the link position.
1. Two joint attachment frames, relative to "l1frame".

~~~

    <link name="link1">
      <frame name="l1frame">
        <pose frame="mframe">0 0 0 0 0 0</pose>
      </frame>
      <pose frame="l1frame">0 0 0 0 0 0</pose>

      <frame name="l1j2frame">
        <pose frame="l1frame">-1 3 0 0 0 0</pose>
      </frame>

      <frame name="l1j1frame">
        <pose frame="l1frame">2 3 0 0 0 0</pose>
      </frame>

    </link>

~~~

Joint 1 is between Link 1 and Link 2. Its frame is relative to l1frame.

~~~

    <joint name="joint1">
      <frame name="j1frame">
        <pose frame="l1j1frame">0 0 0 0 0 0</pose>
      </frame>
      <pose frame="j1frame">0 0 0 0 0 0</pose>
      <parent>link1</parent>
      <child>link3</child>
    </joint>
~~~

Joint 2 is between Link 1 and Link 3. Its frame is relative to "l1frame".

~~~

    <joint name="joint2" type="revolute">
      <frame name="j2frame">
        <pose frame="l1frame">0 0 0 0 0 0</pose>
      </frame>

      <pose frame="j2frame">0 0 0 0 0 0</pose>
      <parent>link1</parent>
      <child>link3</child>
    </joint>

~~~

Link 2 is positioned relative to Joint 1's frame

~~~

    <link name="link2">
      <frame name="l2frame">
        <pose frame="j1frame">0 0 0 0 0 0</pose>
      </frame>
      <pose frame="j1frame">0 0 0 0 0 0</pose>
    </link>

~~~

Link 3 is rotated CCW by 90 degrees. It also has a frame for Joint 3 mounting point.

~~~

    <link name="link3">
      <frame name="l3frame">
        <pose frame="j2frame">0 0 0 0 0 -1.5708</pose>
      </frame>
      <pose frame="l3frame">0 0 0 0 0 0</pose>
      <frame name="l3j1">
        <pose frame="l3frame">3 0 0 0 0 0</pose>
      </frame>
    </link>

~~~

Joint 3 is position on the attach point.

~~~

    <joint name="joint3" type="revolute">
      <frame name="j3frame>
        <pose frame="l3j1" >0 0 0 0 0 0</pose>
      </frame>
      <pose frame="j3frame">0 0 0 0 0 0</pose>
      <parent>link3</parent>
      <child>link4</child>
    </joint>

~~~

Finally, Link 4.

~~~

    <link name="link4">
      <frame name="l4frame">
        <pose frame="j3frame">0 0 0 0 0 0</pose>
      </frame>
      <pose frame="l4frame">0 0 0 0 0 0</pose>
    </link>

~~~

Having all these extra frames is more work, but it makes is simple change link dimensions without having to change multiple poses.

### Challenges

1. The proposed changes makes it more difficult for SDF parsers, because a pose may be defined by a succession of multiple frames. Using the SDF library will shield the user from this added complexity, because it should provide the element lookups to perform this task.
1. Because pose elements are estimated relative to other frame elements, this design introduces the possibility of a circular dependencies, or broken poses.

### Open questions, limitations

1. Should it be possible to define frames in a world file? This could be useful for models defined in the world file, but could prevent a model to be used in any world, unless a default pose is assumed.
1. Is the extra work of defining multiple frames offset by the added benefits? The main benefit is that link geometry can be changed easily,
without having to recompute multiple poses.

### Architecture

The Frame class is responsible for the frame information. Each Frame instance has a parent Frame member.
A valid Frame should have a parent list that never visits a single frame more than once (circular dependency), and the end of the list must point
to the world frame (otherwise the pose cannot be evaluated numerically).

The definition of frames is actually independent of the position of their element in the XML hierarchy. This means that frame elements can be placed in different location in a world or model file, without changing the poses. This is slightly different to the previous behaviour of pose
elements, where the pose is relative to a parent element.

Evaluation of a pose is now done by traversing the list of parents backwards, from the world frame to the parent of the final pose.

Apropriate action must be taken when frames are not found, or circular dependencies are detected:
1. Use gzerr to show a console message when the --verbose is set.
1. Provide a default value for the pose.

Using defined frames will be the recommended way forward, but backwards compatibility will be maintained for pose elements that do not have the frame attribute.

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
    1. case: define a pose that uses the world frame. A pose with a non existing frame.
    1. case: multiple frame elements, and a pose that uses them. A circular reference.
    1. case: poses inside world files that use frames defined in model files.
1. Test: Multiple plots
    1. case: Create two plots with identical data. Saved CSV data from each should be identical

### Pull Requests







