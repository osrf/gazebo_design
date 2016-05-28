## Project: Existing Model Database Design
***Gazebo Design Document***

### Overview

This document describes the existing functionality for
accessing models and other resources from the filesystem
using `GAZEBO_*_PATH` environment variables and
the [gazebosim.org/models](http://gazebosim.org/models)
online model database.
It is a precursor to a document proposing a new design.

### Requirements

Gazebo loads a simulation from a world file specified in SDFormat.
World files can have models directly embedded within them,
but they should also be able to load models from an external
file to promote reuse and reduce code duplication.
Additionally, there are model resources that cannot be expressed
in SDFormat, such as meshes, textures, and plugins
that should be loadable from external files.
These requirements are summarized as follows:

1. Include models, meshes, textures, and plugins in a world file
without specifying their absolute path in the filesystem.
1. Allow models to be included from multiple locations in the
local filesystem.
1. Query an online database for resources if they cannot be found
locally.
1. Keep a cached folder of resources retrieved from the online database.

### Architecture

Include a system architecture diagram.

* Diagram of a filesystem showing the order in which places are checked
for model files (model folders stored in separate locations,
the models cache, and the online database).

### Interfaces

Models can be included in world files
or nested within other models using
`<include>` tags such as the following:

~~~
<include>
  <uri>model://ground_plane</uri>
  <name>different_model_name</name>
  <static>false</static>
  <pose>10 0 0 0 0 0</pose>
</include>
~~~

The `model://` prefix in the `<uri>` tag indicates that the
gazebo model paths should be searched for a resource matching
the supplied value (`ground_plane` in the example above).
Gazebo maintains a list of model paths that includes
`$HOME/.gazebo/models` and the contents of the `:` delimited
environment variable `GAZEBO_MODEL_PATHS`.

Metadata about each model is stored in the `model.config` file.
It includes a model name suitable for display
(typically with capital letters and spaces),
the name of the sdf files for specific sdf versions,
author information
and a description.
An [example](https://bitbucket.org/osrf/gazebo_models/raw/default/cordless_drill/model.config)
is shown below:

~~~
<?xml version="1.0"?>

<model>
  <name>Cordless Drill</name>
  <version>1.0</version>
  <sdf version="1.2">model-1_2.sdf</sdf>
  <sdf version="1.3">model-1_3.sdf</sdf>
  <sdf version="1.4">model-1_4.sdf</sdf>
  <sdf version="1.5">model.sdf</sdf>

  <author>
    <name>John Hsu</name>
    <email>hsu@osrfoundation.org</email>
  </author>

  <description>
    A cordless drill..
  </description>
</model>
~~~


`GAZEBO_*_PATH` environment variables
Describe any new interfaces or modifications to interfaces, where interfaces are protobuf messages, function API changes, SDF changes, and GUI changes. These changes can be notional.

For example:
Plot proto message: A message that carries plot data will be created to transmit data from the server to the client.

Include any UX design drawings.

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
