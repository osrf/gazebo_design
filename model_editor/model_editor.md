## Model Editor for Gazebo
***Gazebo Design Document***

### Overview

The purpose of this project is to create an editor within the Gazebo gui client,
namely gzclient, to enable users to create models without having to manually
create and modify SDFs.

### Requirements

The GUI should enable users to:

1. create and edit one model at a time.
1. add links, visuals, collisions, and joints, sensors, plugins to a model
1. configure properties of each entity listed above.
1. load external meshes, e.g. collada files, and use them as geometry objects
for collisions and visuals.
1. save the model in SDF format.
1. Nice to have: create a copy or an instance of an existing link

### Architecture

**Gazebo GUI Changes**

The project will primarily affect the `gui` component in Gazebo.

A `model_editor` directory will be added which consists of all source code
for the model editor.

**Main Model Editor components**

* Model Creator
    * adds `Links` to the scene. A link is also referred to as a `Part` of a
    model. Supported links include simple shapes and custom meshes.
    * generates and saves the final model SDF.
* Joint Creator
    * creates `Joints` between parts. Supported joint types include revolute,
    revolute2, prismatic, screw, universal, ball joints.
    * handles mouse events as users clicks on links to create joints.
* Part Inspector
    * pops up a non-modal dialog with tabs for configuring visual, collision,
  sensor, plugin properties
* Joint Inspector
    * pops-up a non-modal dialog for configuring joint axis, angle, pose
    properties.
* Model Editor Event
    * contains a collection of model editor specific events that will be fired
    for example when a link is added or a joint is created.
* Model Editor Palette
    * a side panel containing a list of part and part library buttons which users
    can click on to add them to the scene.

**New GUI Tools**

To assist users in creating models in gazebo, a few new gui tools will be added.
For example, creating a vehicle can be challenging without an easy way of
cloning wheels and aligning them with the chassis. The new gui tools aim to
provide a more convenient and intuitive way of accomplishing these tasks.

* Copy and Paste
    * adds copy and paste icons in the gazebo toolbar that enables users to
    copy and paste models/lights.
    * Keyboard shortcuts (`Ctrl+C` and `Ctrl+V`) will also be supported.

* Alignment Tool
    * aligns multiple models with different configurations.
    * Position alignment: Option to align at the minimum/center/maximum position
    of the target model's bounding box along the x, y, and/or z axis.
    * Nice to have: Orientation alignment.

* Snap Tool
    * provides a fast and easy way to snap two models together. For example,
    snapping the flat face of the cylindrical wheel to the side of the vehicle
    chassis.
    * Snapping moves the model only and does not create a joint between the
    models.

**Client-Server communication**

The final model SDF will be published to the `~/factory` topic so that it can be
created on the server.

### Interfaces

Please see [ModelEditor_v4.pdf](ModelEditor_v4.pdf) for the
GUI design of the model editor.

**GUI changes**

* A new menu option `Model Editor` will be added to the `Edit` menu in the
menu bar.
* A new palette consisting of editor items (buttons for adding different parts) will appear on the left side panel when the `Model Editor` mode is
enabled.
* A joint drawing tool will be added to the Toolbar

### Performance Considerations

There may be a small impact on the gazebo client start-up performance as it
will need to create and load the model editor Qt widgets.

The model editor should not affect the server side performance.
Just a note that physics simulation will be paused when the `Model Editor` mode
is on.

### Tests

1. Test: Model Creation
    1. case: Add a part to the scene and verify by querying the scene for the
    visual representing the part.
    1. case: Create a joint between two parts and query the scene to make sure
    the visual representing the joint is created.
    1. case: Create parts and joints, export the SDF, then verify the generated
    SDF by loading it and checking its elements.
1. Test: Inspector
    1. case: Modify part, visual, collision, sensor properties in the
    inspector and make sure that the changes are propagated to the
    model creator object.
    1. case: Modify joint properties in the inspector and make sure that the
    changes are propagated to the joint creator object.
