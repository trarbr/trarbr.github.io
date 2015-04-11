Intro to NancyFx with F#
========================

:date: 2015-04-11
:category: StuffExchange
:tags: F#, FSharp, NancyFx, Nancy

`NancyFx`_ (or just Nancy) is a web application framework for .Net and Mono. I
chose it for `StuffExchange`_ over Web API because of the focus on Mono
compatibility, but didn't really spend much time evaluating it. I'm pretty fond
of it, but unfortunately the documentation is a bit lacking.

.. _NancyFx: http://nancyfx.org/
.. _StuffExchange: {filename}introducing-stuffexchange.rst

To be sure, NancyFx does have documentation, but it's spread pretty thin and is
all C#. That shouldn't be a problem since F# has full C# interoperability, but
as I'm just learning F#, it makes things a bit trickier. Michal Frank wrote the
best `F# centered introduction`_ I could find (unfortunately the code snippets
seem to be missing right now).

.. _F# centered introduction: http://www.mfranc.com/f/f-and-nancy-beyond-hello-world/

Getting started
---------------

The first thing I suggest you do is install the Visual Studio `F# Nancy
Templates`_ (and `F# Web Item Templates`_). Then open Visual Studio, create a
new project and choose the `F# Nancy Applications` template. I pick `Empty
Self-Host`.

.. _F# Nancy Templates: https://visualstudiogallery.msdn.microsoft.com/b55b8aac-b11a-4a6a-8a77-2153f46f4e2f
.. _F# Web Item Templates: https://visualstudiogallery.msdn.microsoft.com/f1dae7fe-1ecc-4f1b-86b5-32a2970d012a

Note that the versions of Nancy referenced in `packages.config` might be out of
date - in my case I get Nancy version 0.17 while Nancy is at 1.1. So I suggest
you go to the Package Manager Console (Tools >> NuGet Package Manager >>
Package Manager Console) and type ``Update-Package`` which will update all
packages in the project.

The template has a couple of files, but the most interesting one is `Program.fs`:

.. code-block:: fsharp

    module NancyIntro.Program
    
    open System
    open Nancy.Hosting.Self
    
    [<EntryPoint>]
    let main args =
        let uri = Uri("http://localhost:3579")
    
        use host = new NancyHost(uri)
        host.Start()
    
        Console.WriteLine("Your application is running on " + uri.AbsoluteUri)
        Console.WriteLine("Press any [Enter] to close the host.")
        Console.ReadLine() |> ignore
        0

I suggest you try building and running the app immediately. I get a
``HttpListenerException``: permission denied. This is because Nancy by default
rewrites localhost URI's to listen on all interfaces, which my system does not
allow. This can be fixed by creating a ``HostConfiguration`` and setting
``RewriteLocalhost`` to ``false``: 

.. code-block:: fsharp

    module NancyIntro.Program
    
    open System
    open Nancy.Hosting.Self
    
    [<EntryPoint>]
    let main args =
        let uri = Uri("http://localhost:3579")
        let configuration = HostConfiguration()
        configuration.RewriteLocalhost <- false

        use host = new NancyHost(configuration, uri)
        host.Start()

        Console.WriteLine("Your application is running on " + uri.AbsoluteUri)
        Console.WriteLine("Press any [Enter] to close the host.")
        Console.ReadLine() |> ignore
        0

If you now get a different ``HttpListenerException`` (can't access file) I
suggest changing the port number in the URI - it's probably because something
else is using that port.

Once it builds and runs, the terminal will show you which address you can
access it on. Point your browser there - you should get a 404 error, since we
haven't defined any routes yet.

Defining a route is pretty easy - you define a type, inherit from
``NancyModule`` and then provide the routes for that module. Add below code
snippet above the ``main`` function (you will also need to ``open Nancy`` to
get access to ``NancyModule``):

.. code-block:: fsharp

    type IndexModule() as x =
        inherit NancyModule()
        do x.Get.["/"] <- fun _ -> box "hello world"

Looks like ``Get`` is a property that returns a dictionary-like object! And it
stores functions! Here we store a function that simply returns `hello world` at
the route `/`. You can now build and run your app again and fire up your
browser. Go to http://localhost:3579 (or whatever address Nancy listens on) and
you should get a plain "hello world" response instead of the 404.

The entire `Program.fs` file now looks like below. You can also checkout the
`entire NancyIntro project`_.

.. _entire NancyIntro project: https://github.com/trarbr/trarbr.github.io/tree/62ee08f0a653e58cf177cdb505c5bb1c6d29b0c5/src/NancyIntro

.. code-block:: fsharp

    module NancyIntro.Program
    
    open System
    open Nancy
    open Nancy.Hosting.Self
    
    type IndexModule() as x =
        inherit NancyModule()
        do x.Get.["/"] <- fun _ -> box "hello world"
    
    [<EntryPoint>]
    let main args =
        let uri = Uri("http://localhost:3571")
        let configuration = HostConfiguration()
        configuration.RewriteLocalhost <- false
    
        use host = new NancyHost(configuration, uri)
        host.Start()
    
        Console.WriteLine("Your application is running on " + uri.AbsoluteUri)
        Console.WriteLine("Press any [Enter] to close the host.")
        Console.ReadLine() |> ignore
        0

This should give you a pretty rough idea of how to use Nancy with F#. I suggest
you check out the other Nancy templates as they show show much more
functionality. I also recommend the mentioned `F# centered introduction`_. I
will also be writing more articles as my `StuffExchange project`_ progresses.

.. _StuffExchange project: {category}StuffExchange
