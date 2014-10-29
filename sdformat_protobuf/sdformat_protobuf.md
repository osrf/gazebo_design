## Project: Convert between sdformat and protobuf messages
***Gazebo Design Document***

### Overview

Currently the `gazebo::msgs` namespace contains numerous functions for creating
protobuf messages from sdf elements,
[for example](https://bitbucket.org/osrf/gazebo/src/8d6519e28f00/gazebo/msgs/msgs.cc#cl-430):
~~~
msgs::MeshGeom MeshFromSDF(sdf::ElementPtr _sdf)
~~~

It would be useful to have helper functions that do the reverse,
generating sdf elements from a protobuf message.
This could be used by the numerous functions in the ServerFixture class
that take in multiple parameters, generate an SDF model description,
and then spawn the model.
Consider [SpawnSphere](https://bitbucket.org/osrf/gazebo/src/8d6519e28/test/ServerFixture.cc#cl-1074)
for example:
~~~
/////////////////////////////////////////////////
void ServerFixture::SpawnSphere(const std::string &_name,
    const math::Vector3 &_pos, const math::Vector3 &_rpy,
    bool _wait, bool _static)
~~~

Another example is the
[SpawnFrictionBoxOptions](https://bitbucket.org/osrf/gazebo/src/8d6519e28/test/integration/physics_friction.cc#cl-92)
class used to simplify spawning boxes in the physics_friction test.
Protobuf messages could be used instead of this custom class.

There is an [open issue](https://bitbucket.org/osrf/gazebo/issue/1028/duplicate-parameter-definitions)
in gazebo about the duplication of parameter definitions
in sdformat and protobuf messages.
This proposal does not attempt to resolve that issue.

### Requirements

Implement helper functions that convert protobuf messages to SDF.
There should be pairs of functions that return:

* a `std::string` of the xml content
* an `sdf::ElementPtr` object

### Architecture
Input: protobuf message

Output: sdformat description as xml string or sdf element object.

### Interfaces
Add helper functions to the `gazebo::msgs` namespace.
One function should convert a protobuf message to a string:
~~~
std::string ToSDF(const msgs::Link &_msg)
~~~
Another function should use that string and return an `sdf::ElementPtr`
~~~
sdf::ElementPtr ToSDF(const msgs::Link &_msg)
{
  std::string sdfString = msgs::ToSDF(msg);
  sdf::ElementPtr sdf(new sdf::Element());
  sdf::initFile("link.sdf", sdf);
  sdf::readString("<sdf version='" SDF_VERSION "'>"
    + sdfString + "</sdf>", sdf);
}
~~~

Consider using Google Protobuf's
 [reflection interface](https://developers.google.com/protocol-buffers/docs/reference/cpp/google.protobuf.message#Reflection),
 which is currently used by gzweb to
 [convert protobuf messages to json](https://bitbucket.org/osrf/gzweb/src/bf45f825f953dac563b20c021c1b6f5241e49f9c/gzbridge/pb2json.cc?at=default).

### Performance Considerations
These helper functions will be convenient for spawning models,
which tends to happen at the beginning of tests in our test suite.
I'm not sure how important performance is for these functions.

### Tests

1. Unit Test: for each message type, generate a protobuf message
    and convert it to an `sdf::ElementPtr` then verify that the
    properties match.

### Pull Requests
This could be done incrementally, as there are many messages that would
need to be converted.
There are many nested messages though
(model, link, collision, surface, friction),
so those should be done in the same pull request.

