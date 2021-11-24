# Fridrich
Fridrich is a project by 3 stupid guys who were bored, so they created a program on which they can vote who of them is the gayest. 
It mainly consists of three parts:
* Fridrich Server
* Fridrich Backend
* Fridrich Dashboard
<br><br><br>
## Fridrich Server
The Server is run on a Raspberry-Pi model 3b+ connected to the local network. It saves all the data in files and accepts requests, handles events like the 0 o'clock vote and some other "cool" stuff. The basic File Layout for the Server should look like this:  
<pre>
|  
|---♦ data  
|   |---♦ chat.json
|   |---♦ Calendar.json
|   |---♦ settings.json
|   |---♦ dVotes.json
|   |---♦ KeyFile.enc  
|   |---♦ KingLog.json
|   |---♦ now.json
|   |---♦ tempData.json
|   |---♦ users.enc
|   |---♦ Version
|   |---♦ yes.json
|  
|---♦ fridrich  
|   |---♦ server
|   |   |---♦ __init__.py
|   |   |---♦ accounts.py
|   |   |---♦ ClientFuncs.py
|   |   |---♦ server_funcs.py
|   |   |---♦ settings.json
|   |   |---♦ UserTools.py
|   |   |---♦ WStationFuncs.py
|   |
|   |---♦ __init__.py
|   |---♦ app_store.py
|   |---♦ cryption_tools.py
|   |---♦ new_types.py
|   |---♦ useful.py
|  
|---♦ FridrichServer.py  
</pre>
The **Calendar.json** file saves the configurations of the calendar in a dict:
```Python 
{'10.10.2005' : ['stuff happened', 'some other things happened as well'], '11.10.2005' : []}
```
**dVotes.json** stores all the data about how many double votes each user has left in this week:
```Python
{'User1':1, 'User2':0}
```
The **KeyFile.enc** is the default key if the client hasn't yet authenticated or sends errors. It is encrypted with the cryption_tools.low class.
**KingLog.json** is the file where all the GayKings are saved (basically a *log*):
```Python
{
    "00.00.0000": "jesus",
    "30.05.2021": "John",
    "31.05.2021": "Will|John|Jack",
    "01.06.2021": "Jack",
}
```
The file **now.json** is used to save all current Votes (in case of a server restart/power off) and in newer versions generally used as the *Votes* Variable. It stores information like this:
```Python
{
    "GayKing":
    {
        "Will": "Trains",
        "John": "Will"
    },
    "BestBusDriver":
    {
        "Will": "Tobi",
        "Margaret": "Simon"
    }
}
```
**tempData.json** is used to transfer temperature data between the main program and the CPUHeatHandler:
```Python
{"temp": 29.0, "cptemp": 38.628, "hum": 39.0}
```
In **users.enc** is a fridrich.cryption_tools.low encrypted dictionary with all users and passwords (low encryption because of speed)<br><br>
The **Version** file stores information about the current version: *Version:0.3.7,MaxLen:20* (Managed by the GUI developer).
**yes.json** is basically the same file as *now.json* but from yesterday.<br><br>
All the files in the **fridrich** folder are just modules for the Server to run.


## Fridrich Backend
The Backend File is meant to be imported by another program (**Fridrich Dashboard**). It is generally used to communicate with the server, get information and send votes.
The File Layout is straightforward:  
<pre>
|  
|---♦ data  
|   |---♦ KeyFile.enc  
|  
|---♦ fridrich
|   |---♦ __init__.py
|   |---♦ app_store.py
|   |---♦ backend.py
|   |---♦ cryption_tools.py
|   |---♦ new_types.py
|   |---♦ useful.py
|  
|---♦ YourProgram.py  
</pre>  
Optionally there also is the file **FridrichBackendOffline.py** which is for testing if you can't connect to a Fridrich Server.
<br><br>
## Fridrich Dashboard
As you may have noticed, this program is not actually included in this repository. The Programmer of it
doesn't want his code to be open-source, so unfortunately you have to make your own program.
As an example of how to use the fridrich module, you can use **VersionChanger.py**, **AppStore.py**
and **adminTool.py**.
<br><br>
## Installation with Docker
There are three docker-images available for Fridrich:

- **Server**: nilusink/fridrich_server
- **BackendAccessPanel**: nilusink/fridrich_backend_access
- ~~**AppStore**: nilusink/fridrich_appstore~~

To run any of the above listed containers, you first need to [install Docker for your
system](https://docs.docker.com/get-docker/).

Then you need to *pull* the container you want to run.<br>Open a terminal and type:
<pre>
docker pull |name of container|:|container version|
</pre>
Instead of *container version*, you can also use *latest* to ensure you have the latest updates of the container.

example:
<pre>
docker pull nilusink/fridrich_server:latest
</pre>
To then *run* the container, type:
<pre>
docker run --rm -it |name of container|:|container version|
</pre>
For the server add 
<pre>
-p 12345:12345
</pre>
Before the docker name (so you can access the port the server uses)<br>
To look up the newest version for each container, follow [this](https://hub.docker.com/u/nilusink) link and click  on the desired repository.

example:
<pre>
docker run --rm -it -p 12345:12345 nilusink/fridrich_server:latest
</pre>

# **Attention!**
This project uses Python-3.10 Syntax (Server and backend), so it won't run on anything else than Python-3.10 or Higher!
