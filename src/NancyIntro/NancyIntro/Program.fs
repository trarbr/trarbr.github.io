module NancyIntro.Program

open System
open Nancy
open Nancy.Hosting.Self
    
type IndexModule() as x =
    inherit NancyModule()
    do x.Get.["/"] <- fun _ -> box "hello world"
    
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
