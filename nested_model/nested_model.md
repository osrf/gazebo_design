## Nested Model for Gazebo
***Gazebo Design Document***

### Overview

The purpose of this project is to support nested models in Gazebo.
Currently SDF supports `<include>` elements that allow users to embed models
inside one another. This is useful as it enables existing SDF's to be reused
when build a more complex model consisting of several parts.
However, there is one drawback. The parser builds a new model by taking all the
links of the included model and appending them to the new model. The
information on the nesting of models is then lost once loaded into Gazebo.
Consequently, the process can not be reversed.

The new approach will enable users to specify `<model>` elements inside
another `<model>` element.

### Requirements

To support nested models, the proposed approach will involve:

1. modifying SDF to support nesting of `<model>` elements.
1. updating Gazebo physics component to support loading and saving of
nested models.
1. adding support for loading and saving nested models in the model editor.
1. extending existing GUI tools to interact with nested models in both
simulation mode and model editor mode.

### Architecture

**SDFormat**

SDF 1.5 description will need to be extended but will remain backwards
compatible.

* `model.sdf`
    * support nesting of models in the sdf description, e.g.

    ~~~
    <element name="model" required="*">

      <element ref="model" required="*">

      </element>

    </element>
    ~~~

* `state.sdf`
    * similar to `model.sdf` - add an element to indicate that it can be nested.

The SDF parser will then be updated to parse the new elements and embed
nested models and model states accordingly.

**Gazebo Physics**

* `Model`
    * enable loading and initialization of nested models and their plugins.
    * add support for packing nested model data into model msgs.
    * Add functions to retrieve nested models, e.g. `Model::GetModels()` and
    `Model::GetModel(const std::string & | unsigned int)`
* `ModelState`
    * maintain and update states of nested models.
* `Entity`
    * implement setting nested model world pose.
* `Link`
    * supporting finding a canonical link in nested models
* `World`
    * update publication of model pose data to include nested models.

The World's `GetModel` function can be used to retrieve a pointer to a nested
model. To get a unique nested model, pass its scoped name as an argument to the
function, otherwise the first nested model with the specified name will be
returned.

Joints to be created between nested models will need the parent link name
and the child link name to be fully scoped.

**Gazebo Rendering**

* `Scene`
    * add support for parsing nested model messages and create visuals with
    the corresponding hierarchical structure.

**Gazebo Msgs**

* `model.proto`
    * add a repeated `Model` field.

**Gazebo Model Editor**

* The model editor will support loading nested models and creating
visuals to represent them. This functionality will be used when:
    * a model is inserted into the editor to become a part of the model
    being edited.
    * an existing nested model in simulation is to be edited in the model
    editor.

* The model palette on the left will display a list of nested models that
are in the editor.

* The Schematic View will create a new node to represent a nested model. The
child models and links of a nested model will not be shown.

* The 3D view will visualize the whole nested model and all child
components (links, joints, collisions, visuals, etc) but they can not be
edited. Similar to SolidWorks, modifications to a nested model (analogous to
an assembly in SolidWorks) will need to be performed in a separate session of
the model editor.

**Gazebo GUI**

The following GUI tools will be extended in order to interact with nested
models:

* Move/Rotate/Scale
* Align
* Snap
* Copy & Paste

The `World` tab in the left panel will also be updated. Specifically, each
model listed under the `Model` category will need to be extended to include
nested models in addition to links. The list will be hierarchical to reflect
nested models at different levels. This also makes it easier for users to
browse and select models and links at each level.

In addition to allowing users to select nested models via the model tree in the
left panel. It is possible to extend the current multi-click entity selection
method in the 3D view to include nested models, i.e. first click selects the
top level model, then subsequent clicks select further into the hierarchy.

The context menu needs to be updated to show different options according to
the nested model's level:

* Top level model
    * Move To
    * Follow
    * Edit model
    * View
    * Copy/Paste
    * Delete
* Intermediate models
    * Move To
    * Follow
    * View
    * Delete
* Lowest level model
    * Move To
    * Follow
    * Apply Force/Torque
    * View
    * Delete
* Link
    * Move To
    * Follow
    * Apply Force/Torque

### Performance Considerations

The overall performance of Gazebo should remain linear to the number of models
in the world.

### Tests

1. Test: Spawning and deleting nested model
    1. case: Spawn a nested model and verify all child models and links are
    loaded.
    1. case: Spawn a nested model and delete it. Verify the nested model and
    all its child models and links are deleted.
1. Test: Loading and Saving
    1. case: Load a world file with a nested model and verify that the nested
    model and its child models are loaded.
    1. case: Load a world file with a nested model then save the simulation.
    Verify that the nested model and its child models are saved.
    1. case: Load a world file with a nested model. Move the nested model then
    save the simulation. Verify the nested model is saved with the correct pose.
1. Test: Canonical link
    1. case: Spawn a nested model and check that there is one canonical link.
1. Test: Nested Model Rendering
    1. case: Spawn a nested model. Check the scene to verify that all models,
    links, visuals, and collisions have a visual representation in the scene.
    1. case: Spawn a nested model and delete it. Check that all corresponding
    visuals are removed from the scene.
1. Test: GUI interaction
    1. case: Copy & Paste a nested model and verify all child models, links,
    visuals, and collisions are copied.
    1. case: Align two nested models and verify alignment by comparing the
    extents of the two bounding boxes.
    1. case: Align a nested models with a normal model (not nested) and verify
    alignment by comparing the extents of the two bounding boxes.
    1. case: Snap a nested model to another nested model. Verify the pose of the
    two nested models.
    1. case: Snap two nested models which share the same root model. Verify
    that it is not possible and the pose of the nested models remain the same.
    1. case: Snap a nested model to a normal model (not nested) and verify the
    the pose of the two models.
    1. case: Move a nested model and verify its new pose. Rotate it and
    verify its pose again.
    1. case: Scale nested model (consisting of a simple shape) and verify
    the new scale of the model and the actual size of the attached object.
