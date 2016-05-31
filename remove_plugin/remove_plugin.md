## Project: Removing plugins via GUI
***Gazebo Design Document***

### Overview

Add buttons to the GUI which let users unload plugins which are currently loaded
in simulation.

### Requirements

1. There should be a GUI element (button, context menu) for each currently
loaded plugin, which when clicked, sends a command to remove the plugin.

1. There must be a way to uniquely identify each plugin so it is clear
which plugin is supposed to be removed.

1. Once the plugin owner receives the request, it should completely unload the
plugin and clear all memory related to it.

1. Once the plugin is removed, a notification is sent to all clients so they
can remove the plugin from their lists.

1. It should be possible to undo the command to delete a plugin, to the effect
that the plugin is reloaded and the simulation state is sent back to the way it
was before the plugin was deleted.

### Architecture

> TODO: Add an image roughly showing that a client sends a user command to
remove a plugin, the plugin owner handles the request, and once the plugin is
removed, the owner notifies all clients about the change.

### Interfaces

Clients send command requests to the server using
[`gazebo::msgs::UserCmd`](https://bitbucket.org/osrf/gazebo/src/default/gazebo/msgs/user_cmd.proto?fileviewer=file-view-default)
messages over the `~/user_cmd` topic.

The message can be extended with a `DELETING` type, and a `repeated string uri`
field. Clients would publish a message to remove a plugin, for example:

    // Advertise topic
    this->dataPtr->userCmdPub =
        this->dataPtr->node->Advertise<msgs::UserCmd>("~/user_cmd");

    .......

    // Publish plugin remove command
    msgs::UserCmd userCmdMsg;
    userCmdMsg.set_description("Remove plugin [" + pluginName + "]");
    userCmdMsg.set_type(msgs::UserCmd::DELETING);
    userCmdMsg.set_uri(plugin->URI().Str());
    this->dataPtr->userCmdPub->Publish(userCmdMsg);

Once the server has handled the deletion, it notifies all clients that the
plugin has been deleted.

> Question: Should we create a new topic for notifying clients?

#### Uniquely identifying plugins

In order to uniquely identify plugins, they could have a URI like the world and
entities, see
[common::URI](https://bitbucket.org/osrf/gazebo/src/default/gazebo/common/URI.hh?fileviewer=file-view-default)
and
[this](https://bitbucket.org/osrf/gazebo/pull-requests/2275/add-uri-class-default/diff#chg-gazebo/physics/Base.hh)
pull request for reference.

URIs for plugins could look like this:

* Model plugin: `data://world/default/model/submarine_buoyant/plugin/buoyancy`
* World plugin: `data://world/default/plugin/wind`
* GUI plugin: `data://client/default/plugin/timer`
* TODO: add others...

### Unloading plugins

* It should be possible to unload a plugin without ending the whole process.
* Plugins can be unloaded on their destructors.
* All memory related to that plugin must be freed (including all smart pointers).
* TODO: We need an API to remove plugins:
    * Who should trigger the plugin deletion? Who is the plugin "owner"?
    * Do models own model plugins?
    * Does the world own world plugins?
    * Does the plugin own itself, so it directly receives a command to remove it?

### GUI

> TODO: Add schematic of the GUI, is it a button, is it a context menu...?


### Performance Considerations

If plugins are not properly cleaned up, it may affect performance.
It would be interesting to add performance tests.

### Pull Requests and tests

Implementation could be broken into the following pull requests, in this order:

1. Implement URI for plugins:
    * Add `Plugin::URI()` function and implement it for each derived class
      `ModelPlugin::URI`, `GUIPlugin::URI`, etc.
    * Add unit tests to verify all URIs are being correctly generated.

1. Make it so plugins are unloaded when destroyed:
    * Uncomment the call to `dlclose` on the destructor.
    * Add unit test creating and destroying a plugin to make sure it is closed.
    * Make other modifications to make sure the test passes for all platforms.
    * Add performance test?

1. Add API for removing plugins
    * Implement API for removing plugins (still TBD)
    * Add unit tests for the new API.

1. Implement client requests to remove plugin:
    * Add fields to `gazebo::msgs::UserCmd`
    * Add delete button to GUI
    * Publish message to `user_cmd` topic when button is pressed.
    * Remove plugin from list when notification about plugin removal is received.
      (topic TBD)
    * Add integration test to
    [test/integration/undo.cc](https://bitbucket.org/osrf/gazebo/src/17b2f08327b287ad319132729d19dffef097cb4e/test/integration/undo.cc?fileviewer=file-view-default)

