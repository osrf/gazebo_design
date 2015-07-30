## Project: SDF reference geometry
***SDF Design Document***

### Overview

Inspired by the ROS tf2 library and Solid Work's reference geometry tools, the Idea is to have the ability to define frames of references in SDF and extend the pose element to have a frame origin.


### Requirements

1. Be able to define reference frames in SDF.
1. Be able to reference that geometry, using the path of the frame element.

### Example

In this example, robot "Robo" is defined in sdf, using frames to define relative poses.

![kinematic chain](links.png)


~~~

<sdf version='1.5'>
  <model name="Robo">
~~~

The version of sdf remains 1.5.

We define a frame named mframe, relative to the world frame.
The world frame always exists, but all other frames need to be defined.
The model frame "mframe" has an offset of x=1 and y=1 with respect to the world frame.
Like in previous versions of SDF, our model "Robo" has a pose element. The pose element has a new attribute, frame, which makes
this pose relative to the "mframe" frame. Therefore the final pose evaluates to x=2 y=1 in the world frame.

~~~
    <frame name="mframe">
      <pose frame='world'>1 1 0 0 0 0</pose>
    </frame>
    <pose frame="mframe">1 0 0 0 0 0</pose>
~~~

Link 1 also defines frames:

1. A baseframe "l1frame" relative to mframe. This is the local link frame.
1. Two joint attachment frames, both relative to "l1frame".

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

Joint 1 is between Link 1 and Link 2. The local frame for this joint is relative to l1frame.

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

Joint 2 is between Link 1 and Link 3. Its frame is also relative to "l1j2frame", the Joint 2 attach frame
on Link 1.

~~~

    <joint name="joint2" type="revolute">
      <frame name="j2frame">
        <pose frame="l1j2frame">0 0 0 0 0 0</pose>
      </frame>

      <pose frame="j2frame">0 0 0 0 0 0</pose>
      <parent>link1</parent>
      <child>link3</child>
    </joint>

~~~

Link 2 is positioned relative to Joint 1 attach frame on link1

~~~

    <link name="link2">
      <frame name="l2frame">
        <pose frame="l1j1frame">0 0 0 0 0 0</pose>
      </frame>
      <pose frame="l2frame">0 0 0 0 0 0</pose>
    </link>

~~~

Link 3 is rotated CCW by 90 degrees. It also has a frame for Joint 3 mounting point.

~~~

    <link name="link3">
      <frame name="l3frame">
        <pose frame="j2frame">0 0 0 0 0 1.5708</pose>
      </frame>
      <pose frame="l3frame">0 0 0 0 0 0</pose>
      <frame name="l4j1frame">
        <pose frame="l3frame">3 0 0 0 0 0</pose>
      </frame>
    </link>

~~~

Joint 3 is positioned on the attach point.

~~~

    <joint name="joint3" type="revolute">
      <frame name="j3frame">
        <pose frame="l4j1frame" >0 0 0 0 0 0</pose>
      </frame>
      <pose frame="j3frame">0 0 0 0 0 0</pose>
      <parent>link3</parent>
      <child>link4</child>
    </joint>

~~~

Finally, Link 4. Note the CW rotation.

~~~

    <link name="link4">
      <frame name="l4frame">
        <pose frame="j3frame">0 0 0 0 0 -1.5708</pose>
      </frame>
      <pose frame="l4frame">0 0 0 0 0 0</pose>
    </link>

~~~

The following diagram shows the frame hierarchy. In this example, the hierachy has no error:

1. Each frame has a parent frame that can be traced back to the world frame.
1. There are no circular dependencies (no frame has itself has a parent).



![frame tree](frame_tree.png)

It is possible to compute the transformation from an origin frame to a destination frame, using the common ancestor for 2 frames:

 1. Use the origin frame as a starting point
 1. Apply the inverse poses of each parent frame until the common ancestor
 1. Apply the direct pose transformation until the destination frame is reached.
 1. The resulting pose is the Pose of the destination frame relative to the origin frame

Having all these extra frames is more work, but it makes it simple to change link dimensions without having to change multiple poses.

When computing transformation between 2 frames, finding the shortest paths between the two transformations should give more precision in transformations than going all the way to the world frame (because it avoids computing unnecessary transformations that can add error).



### Challenges

1. The proposed changes makes it more difficult for SDF parsers, because a pose may be defined by a succession of multiple frames. Using the SDF library will shield the user from this added complexity, because it should provide the element lookups to perform this task.
1. Because pose elements are estimated relative to other frame elements, this design introduces the possibility of a circular dependencies, or broken poses.

### Open questions, limitations

1. Should it be possible to define frames in a world file? This could be useful for models defined in the world file, but could prevent a model to be used in any world, unless a default pose is assumed.
1. Is the extra work of defining multiple frames offset by the added benefits? The main benefit is that link geometry can be changed easily, without having to recompute multiple poses.

### Architecture

## ign-math

Proposition: add a new class to ign-math, named "FrameGraph" that contains the tree of frames. Objects of this type will typically be populated with frames as they are read during the parsing of SDF documents.

1. void AddFrame(const string &_name, const string &_parent, const Pose &_offset);
1. bool ParentFrame(const string &_frame, string &_result);
1. bool Pose (const string &_originFrame, const string &_destinationFrame, Pose &_result);

The GetPose method could also apply a Pose before returning the result, but this operation is easy to perform with the overloaded operator
of Pose.

There is no method to remove a frame, because the typical usage is to add frames while parsing an SDF file, and then use GetPose to evaluate poses that are relative to frames.

## SDFormat changes

The Element class is where the frame information is read from. Each Frame instance has a parent Frame member.

A valid Frame should have a parent list that never visits a single frame more than once (circular dependency), and the end of the list must point to the world frame (otherwise the pose cannot be evaluated numerically). See below for backwards compatibility.

This mechanism will be a modified implmentation of the following function:

~~~
// this is the current version
sdf::Pose sdf::Element::GetValuePose (const std::string &_key = "")

// this is the proposed version. You can specify a relative frame to get the Pose from. By default,
// the absolute position in the world frame is used
sdf::Pose sdf::Element::GetValuePose (const std::string &_key = "", const std::string &_frame="world")

~~~

In order to enumerate the list of frames, the standard sdf::Element and sdf::Param API can be used to identify the correct frame for each Pose Element, and each pose offset from its parent.

A list of all frames encountered during parsing will be maintained, to avoid having to go through all the nodes multiple times. For each frame, the name of the parent frame and the Pose offset should be available directly.

The definition of frames is actually independent of the position of their element in the XML hierarchy. This means that frame elements can be placed in different location in a world or model file, without changing the poses. This is slightly different to the previous behaviour of pose
elements, where the pose is relative to a parent element.

Evaluation of a pose is now done by traversing the list of parents poses backwards, from the world frame to the parent of the final pose.

Appropriate action must be taken when frames are not found, or circular dependencies are detected:

1. Use gzerr to show a console message when the --verbose is set.
1. Provide a default value for the pose.

Using defined frames will be the recommended way forward, but backwards compatibility will be maintained for pose elements that do not have the frame attribute.

The Frame element will also support a "type" or "visual" attribute, to help the gui dislpay axis or coordinate frames.

### Interfaces

1. frame element: This is a new XML SDF element, and its information is available via the sdf::Element API
1. pose element: the frame XML attribute is added to the pose element. The API stays the same.

The sdf::Pose class is not modified. This is because the current Pose is more of a math class (like the ignition math Pose class) than a vehicle to convey frame information. However, it would be possible to extend the sdf::Pose class to expose a list of frames.


### Backwards compatibility

In the current SDF, pose elements do not have a frame attribute. In order to maintain backwards compatibility, the following rules will apply for pose elements when no frame is specified. The following is a list of pose elements and their possible path in the sdf file.

1. <world><include><pose>
1. <world><state><model><pose>
1. <world><light><pose>
1. <sdf/world><actor><pose>
1. <sdf/world><model><pose> A position and orientation in the global coordinate frame for the model. Position(x,y,z) and rotation (roll, pitch yaw) in the global coordinate frame.
1. <sdf/world><model><link><pose> This is the pose of the link reference frame, relative to the model reference frame.
1. <sdf/world><model><link><inertial><pose> This is the pose of the inertial reference frame, relative to the link reference frame. The origin of the inertial reference frame needs to be at the center of gravity. The axes of the inertial reference frame do not need to be aligned with the principal axes of the inertia.
1. <sdf/world><model><link><collision><pose> The reference frame of the collision element, relative to the reference frame of the link.
1. <sdf/world><model><link><visual><pose> The reference frame of the visual element, relative to the reference frame of the link.
1. <sdf/world><model><joint><pose> Pose offset from child link frame to joint frame (expressed in child link frame).

### frame element scoping and Support for nested models

This is ongoing. please add a comment.

### Future improvements

The first step is to implement frames so that they can be specified in sdformat, and loaded by Gazebo.
Support for frames inside Gazebo will come later, and this effort will have its own design. This will include these topics:

1. Where frame information will be displayed for the user
1. 3D feedback for frame origin, and the FrameGraph
1. Upgrades to the Pose message, Join::anchorPose
1. Support in the physics library.
1. Real time updates to the FrameGraph


### Performance Considerations

This design should not impact perfromance much. While there is an added cost to compute each pose element, this cost can be done once when the sdf is loaded.

### Tests

1. Test: FrameGraph in ign math:
    1. case: Return correct Pose when it is relative to the world frame
    1. case: Verify Error when asking for a pose in an unknown frame.
    1. case: Add a frame, and evaluate Poses relative to this frame in the world frame.
    1. case: Add 2 frames and ask for the transform between the 2.
1. Test: reference frames in SDF:
    1. case: define a pose that uses the world frame. A pose with a non existing frame.
    1. case: multiple frame elements, and a pose that uses them. A circular reference.
    1. case: verify that frames work with models defined in a separate sdf file (outside the world file).
    1. case: check that backwards compatibility works when frames are not specified in Pose elements.


### Pull Requests

1. Add the FrameGraph class to the ign math library.
1. Add the Frame and Pose elements to the SDF parser.
1. Add the visual cue to the Frame element so it can be displayed visually by Gazebo







