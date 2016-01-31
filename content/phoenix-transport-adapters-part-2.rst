Phoenix transport adapters, part 2
==================================

:date: 2016-01-31
:category: Phoenix
:tags: Elixir, Phoenix, Channel, Transport, Telly
:summary: a look at Telly, a Phoenix transport adapter for Telnet

This post is an introduction to `Telly`_,
a proof-of-concept transport adapter for the Phoenix framework.
I will show you how I put it together,
and give pointers on how you can customize it to fit your needs.
Let me know if there's anything extra you'd like me to write about.
For part one of this series,
where I talk about Phoenix transport adapters in general,
take a look `here <{filename}/phoenix-transport-adapters-part-1.rst>`_.

.. _Telly: https://github.com/trarbr/telly

If you want to take Telly for a quick spin,
you can use a slightly `modified version`_ of the simple chat example.
I have also recorded a `small video demo`_ showing the functionality.

.. _modified version: https://github.com/trarbr/phoenix_chat_example
.. _small video demo: https://youtu.be/uV6Sx7vQqbI

In the first part of this series we saw that every transport adapter
consists of a server and a handler.
Let's look at these.

The Telly server
----------------

In Telly's case, I'm using `ranch`_ as my server.
ranch is an embeddable TCP server and acceptor pool,
and is also used by Cowboy.
Telly.Supervisor
(which a Telly user must add to the application supervision tree)
is responsible for setting up ranch.

.. _ranch: https://github.com/ninenines/ranch

Let's walk through the ``init/1`` function of Telly.Supervisor:

.. code-block:: elixir

  def init(endpoint) do
    socket_handlers =
      for {path, socket} <- endpoint.__sockets__,
          {_transport, {module, config}} <- socket.__transports__,
          transport_handler = config[:telly],
          serializer = Keyword.fetch!(config, :serializer),
          into: %HashDict{},
          do: {path, {socket, serializer}}

    telly_spec = :ranch.child_spec(make_ref(), 10, :ranch_tcp, [port: 5555], Telly.Transport, [
      endpoint: endpoint,
      handlers: socket_handlers
    ])
    children = [telly_spec]

    Logger.info("Running Telly on port 5555")
    supervise(children, strategy: :one_for_one)
  end

First off,
the supervisor enumerates the list of sockets defined in the endpoint.
For each socket,
it will check if there is a transport with a ``:telly`` transport handler.
If ``transport_handler`` is not nil,
the socket path is added to a HashDict as key,
with the socket and serializer as the value.
The resulting HashDict is saved in ``socket_handlers``.

Next,
Telly.Supervisor creates a child spec for ranch.
Among other things, the child spec tells ranch which port to listen on,
and which module to use as ranch transport (:ranch_tcp).
It also specifies the module of the ranch protocol,
which in this case is Telly.Transport,
Telly's custom ranch protocol.

The last argument is a keyword list.
It will be passed to the ranch protocol when starting it up.

Once the child spec has been generated,
I call supervise/2 to start ranch.

The Telly handler
-----------------

When ranch accepts a new connection it calls ``start_link/4``
in the ranch protocol module -
here it will create a new Telly.Transport process.
Telly.Transport is implemented as a GenServer.
It does quite a bit more work than Telly.Supervisor,
so I'll skim over some parts.

First, ``start_link/4`` invokes ``init/4``:

.. code-block:: elixir

  def init(ref, tcp_socket, tcp_transport, opts) do
    :ok = :proc_lib.init_ack({:ok, self()})
    :ok = :ranch.accept_ack(ref)
    :ok = tcp_transport.setopts(tcp_socket, [{:active, :once}])
    state = %{
      tcp_transport: tcp_transport, # ranch_tcp in this case
      tcp_socket: tcp_socket, # the socket established by ranch
      endpoint: Keyword.fetch!(opts, :endpoint), # the Phoenix Endpoint
      handlers: Keyword.fetch!(opts, :handlers), # all sockets with a :telly handler
    }
    :gen_server.enter_loop(__MODULE__, [], state)
  end

The ``init/4`` function accepts the TCP socket from ranch,
and creates an initial state with the name of the endpoint,
and the ``socket_handlers`` HashMap created above.
After this,
it enters the GenServer loop,
and waits for new messages.
At this point the TCP connection has been established,
but we still don't know which socket handler to use for the connection.

The Telly handler receives a new message when the client sends a new line.
This is first processed by ranch_tcp,
which then sends a message to the Telly handler.
This message invokes ``handle_info/2``:

.. code-block:: elixir

  def handle_info({:tcp, _tcp_socket, data}, %{handlers: handlers} = state) do
    path = String.rstrip(data)

    case HashDict.fetch(handlers, path) do
      {:ok, {handler, serializer}} ->
        state = %{
          tcp_transport: state.tcp_transport,
          tcp_socket: state.tcp_socket,
          endpoint: state.endpoint,
          handler: handler,
          serializer: serializer
        }
        :ok = state.tcp_transport.setopts(state.tcp_socket, [active: :once])
        {:noreply, state}
      :error ->
        {:stop, :shutdown, state}
    end
  end

``data`` is a binary containing the bytes sent from the client.
This is expected to be a socket path,
and is used to fetch the corresponding socket handler and serializer.
These two are then added to the process state.

The Telly handler now know which socket handler to call connect to,
but need to wait for the parameters.
These are expected to arrive as a JSON string in the next message:

.. code-block:: elixir

  def handle_info({:tcp, tcp_socket, data}, %{tcp_transport: tcp_transport, endpoint: endpoint, handler: handler} = state) do
    params =
      String.rstrip(data)
      |> Poison.decode!()

    case Phoenix.Socket.Transport.connect(endpoint, handler, :telnet, __MODULE__, state.serializer, params) do
      {:ok, socket} ->
        Process.flag(:trap_exit, true) # trap exits to avoid crashing if a channel process dies
        if socket.id, do: socket.endpoint.subscribe(self(), socket.id, link: true)
        state = %{
          tcp_transport: tcp_transport,
          tcp_socket: tcp_socket,
          socket: socket,
          channels: HashDict.new(),
          channels_inverse: HashDict.new()
        }
        :ok = tcp_transport.setopts(tcp_socket, [active: :once])
        tcp_transport.send(tcp_socket, "ok\r\n")
        {:noreply, state}
      :error ->
        tcp_transport.send(tcp_socket, "error\r\n")
        {:stop, :shutdown, state}
    end
  end

The Telly handler now knows everything needed connect.
This is done by calling ``Phoenix.Socket.Transport.connect/6``.
``Phoenix.Socket.Transport.connect/6`` calls ``connect/2`` on the socket handler,
and returns a Phoenix.Socket struct if successful.
This struct is added to the process state,
as well as two HashDicts for keeping track of the joined channels.
The Telly handler now sends an "ok" message to the client.

Now, the only thing left is handling messages.
Incoming messages are handled like this:

.. code-block:: elixir

  def handle_info({:tcp, _tcp_socket, data}, %{socket: socket} = state) do
    msg =
      String.rstrip(data)
      |> socket.serializer.decode!([])

    case Phoenix.Socket.Transport.dispatch(msg, state.channels, state.socket) do
      :noreply ->
        {:noreply, state}
      {:reply, reply_msg} ->
        encode_reply(reply_msg, state)
      {:joined, channel_pid, reply_msg} ->
        state = put(state, msg.topic, channel_pid)
        encode_reply(reply_msg, state)
      {:error, _reason, error_reply_msg} ->
        encode_reply(error_reply_msg, state)
    end
  end

Very simple, right? ``encode_reply/2`` simply encodes the message,
sends it to the client,
and returns a ``{:noreply, state}`` tuple to the GenServer.

Outgoing messages are handled like this:

.. code-block:: elixir

  def handle_info({:socket_push, _encoding, _encoded_payload} = msg, state) do
    reply(msg, state)
  end

That was pretty much a complete tour of Telly.
There are a few more bits,
but I'll leave you to explore those on your own.
Let me know if you want me to write about any of it.

Customization and tradeoffs
---------------------------

As noted, Telly is just a proof of concept.
I wrote it to learn how transport adapters work,
and what is needed to make my own.
I have made plenty of tradeoffs in the name of keeping things simple,
so I will end this post by talking about what can be improved,
or just different,
depending on your use case.

First,
Telly is hardcoded to listen on port 5555.
It's probably a good idea to make that configurable,
so it can be specified in the applications config.

Second,
the transport handler for Telly is hardcoded to be Telly.Transport.
In fact,
the application developer should be choose the handler for a transport,
on a socket by socket basis.
This is done by specifying a different handler in the ``transport/2`` macro.
To accomodate this, the current handler should be split in two parts:
a broker, and the actual handler.
The job of the broker is to wait for the client to specify the socket path.
The transport handler can be deduced from the the socket path.
All further messages should be dispatched to that handler.
The transport handler must be added to ``socket_handlers`` in Telly.Supervisor.

Third,
if you are implementing a transport adapter for a specific protocol,
you may not be able to specify a path and parameters with custom messages.
For example,
the MQTT protocol does not expect different kinds of handlers,
and the client will send username and password in the first packet.
In this case, you might need to listen on separate ports for each socket,
so you know that a connection on port X is for socket handler Y.
That means you need a separate ranch child spec for each socket.
It also means the port should be specified as an option in the transport macro,
and not through the global configuration.

Fourth,
Telly depends on the connection parameters being specified as JSON.
This might not apply in your situation.
In the MQTT example,
you'd probably extract these from the username and password fields.

Fifth,
it's not very Telnet-like to send JSON strings back and forth.
It would be more typical to send commands.
Something like: "CONNECT {{socket path}} {{params}}", "JOIN {{topic string}}"
and "BROADCAST {{topic string}} {{message}}" might be more fitting.

Lastly,
I have not yet tested Telly with long strings.
What happens if the message is longer than a TCP packet?
Does ranch wait for a new packet and parse it until the line break,
or will Telly have to handle this?
I don't know!

That concludes this series for now.
I'm not sure what I'll do with Telly now.
Part of me wants to address points 1, 2 and 5 and 6 above,
to build a better Telnet transport adapter.
On the other hand,
I want to try and tackle MQTT.
Unfortunately,
I have to put it on the back burner for a while,
but let me know if you have any requests,
or any feedback in general.
