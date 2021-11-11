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
|   |---♦ __init__.py
|   |---♦ Accounts.py
|   |---♦ AppStore.py
|   |---♦ cryption_tools.py
|   |---♦ FanController.py
|   |---♦ new_types.py
|   |---♦ ServerFuncs.py
|   |---♦ settings.json
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
|   |---♦ AppStore.py
|   |---♦ backend.py
|   |---♦ cryption_tools.py
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
There are two docker-images available for Fridrich:

- **Server**: 0a927ce7c3a644f32268cd65ea04b6354b94b98dbd484df36e2293bd9f09e790
- **BackendAccessPanel**: de59181f07041c59e53d8e90632576b40c127d58aa72491c99070508fe724941

To run any of the above listed containers, you first need to [install Docker for your
system](https://docs.docker.com/get-docker/). <br>
To then run the container, open a terminal and type:
<pre>
docker run --rm -it |sha256 value of container|
</pre>
For the server add 
<pre>
-p 12345:12345
</pre>
before the sha value (so you can access the port the server uses)
# **Attention!**
This project uses Python-3.10 Syntax (Server and backend), so it won't run on anything else than Python-3.10 or Higher!
