## Project: SDF reference geometry
***SDF Design Document***

### Overview

Inspired by Solid Work's reference geometry tools, the Idea is to have the hability to define frames of references (first) in SDF and reference them from extended pose elements.


### Requirements

1. Be able to define reference geometries inside the following elements: model, link, visual.
1. Provide a type to help with visualization (axis, or frame)
1. Be able to reference that geometry, using the path of the frame element.

### Example





### Challenges

1. The proposed changes makes it more difficult for SDF parsers, because a pose may be defined by a succession of multiple frames. Using the SDF library will shield the user from this added complexity, because it should provide the element lookups to perform this task.
1. Because pose elements are estimated relative to other frame elements, this design introduces the possibility of a circular dependencies.

### Open questions, limitations

1. Should it be possible to define frames in a world file? This could be useful for models defined in the world file, but could prevent a model to be used in any world, unless a default pose is assumed.

### Architecture




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


Keep in mind that smaller, atomic pull requests are easier to review.


