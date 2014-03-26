# ZeroMQ-based transport library for Gazebo
***Gazebo Design Document***

## Overview

Gazebo's current transport library was designed and implemented in house.
Although it has been working for years and it's fast, there are quite a few
existing projects that we could use for replacing our custom approach. The
main advantage that we will get by using an existing transport alternative is a
fewer amount of code to maintain in Gazebo.

[ZeroMQ](http://zeromq.org) seems to be a good candidate for implementing the
core functionality of the transport system. ZeroMQ essentially provides framing
and portability to sockets. Another interesting features are its large
collection of bindings, LGPL license, active community, and simplicity of use.

## Requirements

The main requirement of this library is to expose an API for communicating
with the Gazebo components via topics or service calls. A client of this library
might be located inside one of the Gazebo processes or in an external process
(command line tool), even in a different machine. Essentially, this is the main
functionatility that the transport library should provide:

1. Allow a client to advertise, subscribe, and publish a topic.
1. Allow a client to request/response service calls.

## Architecture

There are interesting topics to discuss along the lines of this
project: type of architecture and how to solve the discovery, transport and
serialization problems.

### Centralized Vs Distributed architecture

Gazebo's current approach is based on a centralized model where a dedicated
process registers the addresses of the components advertising every topic or
service call. A distributed approach doesn't rely on this dedicated process
removing the single point of failure.

We are proposing a transition to a distributed architecture where all components
create a peer to peer network for distributing the discovery
information across the network. It will be important to take into consideration
the performance and scalibility of the distributed approach when the number of
clients grow. Once the clients' location have been discovered, the data
communication is performed by using the data delivery capabilities of ZeroMQ
between the interested parties. The rest of clients do not participate in the
data communication.

### Discovery

This is the process required to know the adress associated to the
publisher of a topic or service call. Centralized architectures implemente this
by quering the master process. In a distributed architecture we need a discovery
process. ZeroMQ does not provide a discovery protocol, so we propose a custom
one.

A discovery message is composed by two main parts: header and body.

**Packet format: Header.**

      0               1               2               3
      0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |             Version            |              GUID            /
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     /                           GUID (cont)                         /
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     /                           GUID (cont)                         /
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     /                           GUID (cont)                         /
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     /              GUID              |  Topic length |              /
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
     |                                                               |
     .                                                               .
     .                     Topic name (max 192 bytes)                .
     .                                                               .
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |     Type       |                    Flags                     /
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                           Flags (cont)                        |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                           Flags (cont)                        |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                           Flags (cont)                        |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |  Flags (cont)  |
     +-+-+-+-+-+-+-+-+-

**Packet format: Body.**

         0               1               2               3
      0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |         Address length         |                              /
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-                              +
     |                                                               |
     .                                                               .
     .                   ZeroMQ address (max. 267 bytes)             .
     .                                                               .
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

#### Message overview ####

The discovery protocol is composed by two main type of messages: Advertisement
and Subscription. The Advertisement message is used to advertise the ZeroMQ
address associated to a topic or service call. The Subscription message is used
to request the ZeroMQ address information associated to a given topic. An
Advertisement message can be sent proactively by a publisher when it joints the
network, periodically as a hearbit, or as an aswer to a Subscription message.

Next are the four available messages for the discovery protocol:

* Advertisement message.

  Header (type = 1) + Body.

* Advertisement-service-call message.

  Header (type = 3) + Body

* Subscription message.

  Header (type = 2).

* Subscription-service-call message.

  Header (type = 4).

All bytes of data are sent over the network using little endian. The port used
for the discovery protocol is 11345.


#### Protocol Overview ####

The discovery protocol is implemented by using UDP broadcast
to communicate the discovery information between all the clients. When a new
client advertises a topic or service call, it sends an Advertisement or
Advertisement-service-call message. This message will be received by the other
transport clients, that will update its discovery information with the data
contained in the message.

When a new client needs to subscribe to a topic or service call, it first checks
if the information is already available (due to a previous Advertisement
message). If the client does not know the location of the other client
publishing the topic or providing the service, a subscription message is
broadcasted, requesting the owner of this topic to send an Advertisement
message.


An alternative discovery might be implemented using
[zbeacon](http://czmq.zeromq.org/manual:zbeacon).

#### Transport

ZeroMQ supports the concept of publish/subscribe to a string topic. From the
subscriber's perspective, the subscription is performed by executing a connect()
call passing the publisher's ZeroMQ address as a parameter. After the connect(),
the client will receive updates each time the publisher sends new data.

#### Serialization

Gazebo currently uses
[Google Protocol Buffers](https://developers.google.com/protocol-buffers/) for
serializing data and this project will keep using protobufs for the
serialization step.

### Code design ###

The code of the transport library will be stored in a separate repository, and
will result in a separate and Gazebo-independent debian package.

The external dependencies will be Google protobufs and ZeroMQ 3.x. We will use
the C++11 standard.

The code will be divided in the next files:

* gazebo/transport/TransportIFace.hh: Public API to be used by the clients of the
transport library. All the methods will be declared pure virtual and the intent
is to have an API independent of the implementation. There will be no references
to ZeroMQ in this file.

* gazebo/transport/NetUtils.hh/cc: Helper class for networking issues (IP address
of the current machine, check if an IP address is private).

* gazebo/transport/TopicsInfo.hh/cc: Class that will maintain the current
knowledge that a client will have for each topic/service. It will store if the
client is connected to the publisher of a given topic, if it's subscribed, if
a topic is advertised by itself, if a service has been requested, callback
information.

* gazebo/transport/Packet.hh/cc: Helper class used to manage all the discovery
messages.

* gazebo/transport/Discovery.hh/cc: Class used to manage all the discovery
protocol.

* gazebo/transport/zeromq/ZmqTransport.hh/cc: ZeroMQ-based implementation of
transport public API.

* gazebo/transport/zeromq/ZmqTransport.hh/cc: ZeroMQ-based implementation of
transport public API.

## Interfaces

The public transport API will be declared in gazebo/transport/TransportIFace.hh
and will provide the following methods:

1. (un)advertise(topic)
1. (un)subscribe(topic, cb)

    cb(topic, msg)

1. publish(topic, msg)

1. (un)advertise_service(topic, cb)

    rep <- cb(topic, req)

1. rep <- request(topic, req, timeout)
1. request_async(topic, req, cb)

    cb(topic, rep)

A msg is defined as protobuf message.

## Performance Considerations ##

The performance considerations are important because of the extensive usage of
this library in Gazebo. Two main optimizations have to be addressed:

1. Ensure zero copy when publisher/subscriber are within the same process.
1. Ensure that no serialization/deserialization is performed when publisher and
subscriber are within the same process.

## Tests ##

1. Test: Check communications running a pub/sub example in the same thread.
    1. case: Expect that publish will not succeed without a prior advertise().
    1. case: Create a transport node, subscribe, advertise, and publish.
    1. case: unadvertise the topic and publish. Expect that publish will not
    succeed.

1. Test: Repeat the first test with publisher and subscriber running on
different threads.

1. Test: Repeat the first test with publisher and subscriber running on
different processes.

1. Test: Test the publication/subscription of a large number of messages in a
short period of time.

1. Test: Test the publication/subscription of messages containing large data.

1. Test: Check communications running a service call req/rep example in the same
thread.
    1. case: Expect that the request will not succeed without a prior
advertise().
    1. case: Create a transport node, advertise, and request a service call.
    1. case: unadvertise the service topic and request. Expect that request will
    not succeed.

1. Test: Repeat the first service call request running on different
threads.

1. Test: Repeat the first service call request running on different processes.

1. Test: Test with several clients requesting the same service call
concurrently.

Open questions:

1. How to test the communication between different machines on the same LAN?
1. How to test the commuinication between different machines on different LANs?
