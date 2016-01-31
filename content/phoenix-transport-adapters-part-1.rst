Phoenix transport adapters, part 1
==================================

:date: 2016-01-30
:modified: 2016-01-31
:category: Phoenix
:tags: Elixir, Phoenix, Channel, Transport, Telly
:summary: a quick look at the machinery of Phoenix transport adapters

This series takes a look at building custom transport adapters
for the Phoenix framework (currently at version 1.1).
This post is an introduction to Phoenix transport adapters.
I briefly describe what a transport adapter does,
and what is needed to implement one.
In the next post in this series I will use Telly as example
of how you can write an adapter.
Telly is a proof-of-concept transport adapter,
and uses Telnet as the underlying protocol.

Phoenix is the name of a neat web framework written in Elixir.
It is called a "framework for the modern web"
because it focuses on two-way client-server communication,
in addition to plain HTTP request/response.

The Phoenix feature powering two-way communication is called Channels.
And they are awesome.
They make it very easy to create applications with two-way communication,
and everything happens in soft real-time.
And the best thing is: they do it in a transport-agnostic way.
This makes it very simple to integrate different devices!
Imagine web applications where users connect over Websocket to
monitor and control their IoT devices,
which are connected over some efficient M2M (machine-to-machine) protcol.
You can learn more about Channels in the `official Channel guide`_.

.. _official Channel guide: http://www.phoenixframework.org/docs/channels

If you're new to Phoenix channels,
I'd suggest checking out `simple chat example`_,
a simple web application for chat built using channels.
From this point on,
I will assume you are passingly familiar with the channel terminology.

.. _simple chat example: https://github.com/chrismccord/phoenix_chat_example

In brief, adding a channel to a Phoenix app requires the developer to:

- add a `socket` to endpoint.ex,
  identifying a `socket path` and `socket handler`.
  The socket handler is an Elixir module
  (e.g. web/user_socket.ex in the simple chat example),
  and contains code to authenticate and identify connections on that socket.
- add one or more channels in the socket handler,
  that can be used from the socket.
  The channel specifies a `topic string`
  (which can contain wildcards),
  and the channel module handling messages for the given topic string.
  This is done with the ``channel`` macro.
- add one or more transport adapters in the socket handler,
  by specifying the `transport name` and the adapter module.
  This is done with the ``transport`` macro.

From this, we can get an idea of what is required to create a custom transport.
First, you must select a transport name.
Phoenix ships with `:longpolling` and `:websocket` out of the box,
so using the name of the protcol as transport name might be a good idea.

Next, you need to write the actual transport adapter. It must be able to:

- receive connect requests and dispatch those to the correct socket handler.
  Your adapter must have some means of identifying the socket handler.
  This is mostly done using the socket path,
  which will be specified by the connecting client [#]_.
  In addition to the socket handler,
  the adapter must also obtain any parameters needed when connecting.
- once connected,
  decode and dispatch incoming messages from the client.
  The actual dispatch is done by the Phoenix.Socket.Transport module.
- keep track of channels which have been joined on the socket,
  and their associated pids.
  Joining a channel creates a channel process,
  and all further messages sent on that topic must be dispatched
  to that channel process.
- encode and forward outgoing messages to the client.

There are two parts to every transport adapter: a server and a handler.
The server must be started as part of your application,
and must listen for requests from clients.
These requests should then be dispatched to your transport handler.
The handler acts as a translator between your protocol
and the Phoenix channel protocol.
It connects on the socket handler,
keeps track of joined channels,
dispatches incoming messages,
and forwards outgoing messages.

Encoding and decoding is done by a serializer module.
You can either build a custom one for your transport,
or use a serializer that ships with Phoenix.
Maybe you want to use protocol buffers?
Write a serializer for that,
and ship it with your transport!

The default configuration for your transport adapter is specified in the
adapters ``default_config/0`` function. It must return a keyword list,
and should at least specify the default handler for your transport,
as well as the default serializer.

How to implement the transport handler will depend on your protocol,
and the circumstances you're using it under.
For example,
handling connect requests with Websockets is pretty straightforward.
Here the socket path can be specified in the URL,
while the connect parameters can be passed in the query string.
It is not as straightforward with all protocols.
When using a raw TCP protocol you have the freedom to implement whatever
solution suits your problem best.

As an example of a custom transport adapter I will take a look at `Telly`_.
Telly is a transport adapter for the Telnet protocol,
and in the next post I'll write about the details of it.
It should help you build your own adapters for other protocols.

.. _Telly: https://github.com/trarbr/telly

.. [#]

  You could use other means for identifying the socket handler.
  For example,
  you could use a unique TCP port for each socket.
  The port could be a configuration option for the transport handler,
  and could be specified by a developer when adding it to the socket handler.