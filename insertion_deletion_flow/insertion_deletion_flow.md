# Insertion and deletion flow
*Gazebo design document*

This document describes the problems with the way we're currently handling
entity insertion and deletion requests in Gazebo and proposes a new
implementation.

## Problems with current approach

* `gazebo::transport::requestNoReply(<node>, "entity_delete", <name>)` requests
are being sent back and forth with different intentions. This opens way for
several issues, including cyclic calls and message misinterpretation.

    > For example, `gui::ModelRightClickMenu` sends a
    > [request](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/gui/ModelRightMenu.cc?fileviewer=file-view-default#ModelRightMenu.cc-330)
    > to delete an entity, then once it is deleted,
    > `physics::Entity::Fini`
    > [sends](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/physics/Entity.cc?fileviewer=file-view-default)
    > the same request to notify everyone that it has been deleted.

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
    > called "name". If we want to delete just the model, we send a request to delete
    > entity "name", so both will end up being
    > [deleted](https://bitbucket.org/osrf/gazebo/src/0cc955fdbe127572a5355c67f103f6d39d3e3350/gazebo/physics/World.cc?fileviewer=file-view-default#World.cc-2574).

* Several classes in `gzclient` are handling deletion independently, which means
there are several points of entry to maintain. That's not really a problem, but
something we should be aware of.

    > [rendering::Scene](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/rendering/Scene.cc?fileviewer=file-view-default#Scene.cc-2503),
    > [gui::ModelListWidget](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/gui/ModelListWidget.cc?fileviewer=file-view-default#ModelListWidget.cc-2594) and
    > [gui::GLWidget](https://bitbucket.org/osrf/gazebo/src/0a567e9285875359108a15f3be678dea8f8fb5bc/gazebo/gui/GLWidget.cc?fileviewer=file-view-default#GLWidget.cc-1267)
    > are listening to `entity_delete`.

## Desired flow

* Anyone can request a deletion / insertion: the server itself, clients, plugins
running in the server, standalone programs, etc.

* All requests should be handled the same way by the server, going through the
same pipeline (i.e. share a common point of entry and exit in the server).

* It should be clear which entity is targeted, no matter its type (model, light, link...).

* Requests should be handled in the order they arrive. This is not limited to
insertion/deletion, but also includes things like pose change.

* After a request has been fulfilled, the server notifies everyone else about it
in a unified way.

The flow is captured in this image:

![Flow](https://bitbucket.org/osrf/gazebo_design/raw/insertion_deletion_flow/insertion_deletion_flow/flow.png)

## Proposal

### Requests to the server (blue arrows)

A new message type will be created, which can be used for all kinds of requests
and notifications. For example:

    package gazebo.msgs;

    import "factory.proto";

    /// \ingroup gazebo_msgs
    /// \interface Operation
    /// \brief A message containing a single operation, specified by type.
    /// The operation data will be contained in another field.
    /// It can be used to request that an operation is performed, or to
    /// notify it has been performed, for example. For example:
    ///
    /// if (msg.type() == DELETE_ENTITY)
    /// {
    ///   if (msg.has_uri())
    ///     <perform deletion>
    ///   else
    ///     gzwarn << "Message does not contain URI, which is required for deletion operation.\n";
    /// }

    message Operation
    {
      /// \brief Types of operations.
      enum Type
      {
        /// \brief Deleting an entity.
        DELETE_ENTITY = 1;

        /// \brief Inserting an entity.
        INSERT_ENTITY = 2;
      }

      /// \brief Type of operation.
      required Type type = 1;

      /// \brief Entity URI in string format, for delete operations for example.
      optional string uri = 2;

      /// \brief Factory message, for insert operations.
      optional Factory factory = 3;
    }

#### Block A

`physics::World` will advertise a `/request` service which takes an `Operation`
message. For example:

    ignition::transport::Node ignNode;
    std::string service = "/request";

    ignNode.Advertise("/request", &World::RequestService, this);

    void World::RequestService(const gazebo::msgs::Operation &_req,
        gazebo::msgs::Empty &/*_rep*/, bool &/*_result*/)
    {
      // Add request to queue
      std::lock_guard<std::mutex> lock(this->dataPtr->requestsMutex);
      this->dataPtr->requests.push_back(msg);

      // No response is sent here, otherwise only the requester would be
      // notified.
    }

Internally, all requests, independently of type, are placed in a single queue.
The queue is processed in order at each `World::Step`.

* As part of the model destruction, some events might be triggered (which result
  in work to do in other threads, such as the sensor thread). This might need
  better synchronization or not.

#### Block B

Clients can perform requests as follows:

    std::function<void(const gazebo::msgs::Empty &, const bool)> unused =
      [](const gazebo::msgs::Empty &, const bool &)
    {
    };

    msgs::Operation req;
    req.set_type(msgs::Operation::DELETE_ENTITY);
    req.set_uri(<entity uri>);

    ignition::transport::Node ignNode;
    ignNode.Request("/request", req, unused);

Requests can be sent directly from any widget in the client.

##### Request helpers

Due to the nature of ignition services, every request must provide a response
callback function, even if we don't care about the reply. That's why we needed
the `unused` lambda in the example above.

None of the requests proposed in this design require responses. So every
request would need to create a function which won't be used. That can become
quite cumbersome and repetitive, especially compared to the current
single-lined `gazebo::transport::requestNoReply()`.

Possible solutions:

* Add a feature to Ignition Transport: the possibility of making requests which
don't require responses to

* Add helper functions to Gazebo, for example:

  void transport::ignRequestEntityDelete(const std::string &_uri)
  {
    // Unused callback
    std::function<void(const gazebo::msgs::Empty &, const bool)> unused =
      [](const gazebo::msgs::Empty &, const bool &)
    {
    };

    msgs::Operation req;
    req.set_type(msgs::Operation::DELETE_ENTITY);
    req.set_uri(_uri);

    ignition::transport::Node ignNode;
    ignNode.Request("/request", req, unused);
  }

### Notification to clients (red arrows)

#### Block C

If deletion / insertion is successfully completed, the server notifies everyone
else through a normal topic:

    // Notify deletion is complete
    ignition::transport::Node ignNode;
    std::string topic = "/notification";
    ignNode.Advertise<gazebo::msgs::StringMsg>(topic);

    gazebo::msgs::Operation msg;
    req.set_type(msgs::Operation::DELETE_ENTITY);
    /// \param[in] _service
    msg.set_uri(<entity uri>);
    ignNode.Publish(topic, msg);

* Notifications about deletion can be sent from the `Entity::Fini` method, so
every entity deleted, independently of type (models, links, lights...) will
notify the same way. (Using `Fini` is safer than destructors, because by the
time we reach the destructor, the object's internal state might have already
been cleaned up, so transport for example might not be available anymore).

* Notification about insertion can be sent in the end of each `<Entity>::Load`
method (i.e. `Model::Load`, `Link::Load`, etc), which is when we're sure the
entity has been completely loaded without issues.

#### Block D

Each client has the responsibility of handling these in order. In `gzclient` for
example, each widget can independently subscribe to the `/notification` topic.
For example:

    void OnNotification(const gazebo::msgs::Operation &_msg)
    {
      // Handle deletion/insertion/moving now that we have confirmation, not
      // when it was requested
    }

    ignition::transport::Node ignNode;
    ignNode.Subscribe("/notification", OnNotification);

### Deprecations

* `gazebo::transport::requestNoReply(<node>, "entity_delete", <name>)` used as
a request will be deprecated in Gazebo 8 and removed in Gazebo 9.

* `gazebo::transport::requestNoReply(<node>, "entity_delete", <name>)` used as
a notification will be removed in Gazebo 8.

### Pull requests

(The order and grouping might change)

1. Deletion request service and notification topic.

2. Insertion request service and notification topic.

3. Rearranging queue in server.

4. Rearranging queue in client.

