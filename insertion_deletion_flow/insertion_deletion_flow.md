# Insertion and deletion flow
*Gazebo design document*

This document describes the problems with the way we're currently handling
entity insertion and deletion requests in Gazebo and proposes a new
implementation.

## Problems with current approach

* `entity_delete` requests are being sent back and forth with different
intentions. This opens way for several issues, including cyclic calls and the
misinterpretation of the messages.

> For example, `gui::ModelRightClickMenu` sends a
> [request](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/gui/ModelRightMenu.cc?fileviewer=file-view-default#ModelRightMenu.cc-330)
> to delete an entity, then once it is deleted,
> [`Entity::Fini`](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/physics/Entity.cc?fileviewer=file-view-default)
> sends the same request to notify everyone that it has been deleted.

* We're not respecting the order in which insertion and deletion requests are
made.

> For example, as `physics::World` receives requests to
> [insert](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/physics/World.cc?fileviewer=file-view-default#World.cc-1288)
> or
> [delete](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/physics/World.cc?fileviewer=file-view-default#World.cc-1575)
> an entity, it places them in separate queues, which possibly changes the order
> in which they are
> [processed](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/physics/World.cc?fileviewer=file-view-default#World.cc-2300).

* `entity_delete` requests specify the entity's scoped name, which may cause
wrong behaviour in case entities of different types have overlapped names.

> For example, we have a world containing a model called "name" and a light also
> called "name". If we want to delete just the model, both will end up being
> [deleted](https://bitbucket.org/osrf/gazebo/src/0cc955fdbe127572a5355c67f103f6d39d3e3350/gazebo/physics/World.cc?fileviewer=file-view-default#World.cc-2574).

* Several classes in `gzclient` are handling deletion independently, which means
there are several points of entry to maintain.

> [rendering::Scene](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/rendering/Scene.cc?fileviewer=file-view-default#Scene.cc-2503),
> [gui::ModelListWidget](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/gui/ModelListWidget.cc?fileviewer=file-view-default#ModelListWidget.cc-2594) and
> [gui::GLWidget](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/gui/GLWidget.cc?fileviewer=file-view-default#GLWidget.cc-1267)
> are listening to `entity_delete`. Is there a problem here?

## Desired flow

* Anyone can request a deletion / insertion: the server itself, clients, plugins
running in the server, standalone programs, etc.

* All requests should be handled the same way, going through the same pipeline.
(i.e. share a common point of entry and exit in the server)

* The targeted entity should be clear, despite its type (model, light, link...).

* Requests should be handled in the order they arrive. This is not limited to
insertion/deletion, but also includes things like pose change.

* After a request has been fulfilled, the server notifies everyone else about it
in a unified way.

The flow is captured in this image:

![Flow](https://bitbucket.org/osrf/gazebo_design/raw/insertion_deletion_flow/insertion_deletion_flow/flow.png)

## Proposal

### Requests to the server

For deletion, `physics::World` will advertise an entity delete service which
takes the entity's unique `common::URI`. For example:

    void World::EntityDeleteService(const example::msgs::StringMsg &_req,
      example::msgs::StringMsg &/*_rep*/, bool &_result)
    {
      // Handle deletion internally
      _result = AddDeletionToQueue(_req.entity_uri());

      // No response is sent here, otherwise only the requester would be
      // notified.
    }

    ignition::transport::Node node;
    std::string service = "/entity_delete";

    node.Advertise(service, EntityDeleteService))

For insertion, `physics::World` advertises a factory service, which takes an
SDF string. For example:

    void World::FactoryService(const example::msgs::StringMsg &_req,
      example::msgs::StringMsg &/*_rep*/, bool &_result)
    {
      // Handle insertion internally
      _result = AddInsertionToQueue(_req.entity_sdf());

      // No response is sent here, otherwise only the requester would be
      // notified.
    }

    ignition::transport::Node node;
    std::string service = "/factory";

    node.Advertise(service, FactoryService))

Internally, all requests, independently of type, are placed in a queue. They
could be stored as protobuf messages for example. The queue is processed in
order at each `World::Step`.

Clients can perform requests as follows:

    // Request deletion
    ignition::transport::Node node;
    example::msgs::StringMsg req;
    req.set_entity_uri(uri);
    node.Request("/entity_delete", req, <no callback>);

### Response to clients

If deletion is successfully completed, the server notifies everyone else through
a normal topic:

    // Notify deletion is complete
    ignition::transport::Node node;
    std::string topic = "/notify/deletion";
    node.Advertise<example::msgs::StringMsg>(topic);

    example::msgs::StringMsg msg;
    msg.set_entity_uri(uri);
    node.Publish(topic, msg);

The same goes for insertion:

    // Notify insertion is complete
    ignition::transport::Node node;
    std::string topic = "/notify/factory";
    node.Advertise<example::msgs::StringMsg>(topic);

    example::msgs::StringMsg msg;
    msg.set_entity_sdf(sdf);
    node.Publish(topic, msg);

Each client has the responsibility of handling these in order. For `gzclient`,
it might be interesting to have one point of entry for the notifications
coming from the server, and from there, events are fired notifying each
individual widget. Or each widget can independently subscribe to the topics.

This is how they subscribe to notifications:

    void OnDeletionNotification(const example::msgs::StringMsg &_msg)
    {
      // Handle deletion now that we have confirmation, not when it was
      // requested
    }

    ignition::transport::Node node;
    std::string topic = "/notify/deletion";
    node.Subscribe(topic, OnDeletionNotification);

### Deprecations

* `entity_delete` used as a request will be deprecated in Gazebo 8 and removed
in Gazebo 9.

* `entity_delete` used as a notification will be removed in Gazebo 8.

### Pull requests

(The order and grouping might change)

1. Deletion request service and notification topic.

2. Insertion request service and notification topic.

3. Rearranging queue in server.

4. Rearranging queue in client.

