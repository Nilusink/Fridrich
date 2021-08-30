# Fridrich
Fridrich is a project by 3 stupid guys who were bored so they created a programm on wich they can vote whom of them is the gayest.
It mainly consist of three parts:
* Fridrich Server
* Fridrich Backend
* Fridrich Dashboard
<br><br><br>
## Fridrich Server
The Server is run on a Raspberry-Pi model 3b+ connected to the local network. It saves alle the data in files and accepts requests, handels events like the 0 o'clock vote and some other "cool" stuff. The basic File Layout for the Server should look like this:  
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
|---♦ modules  
|   |---♦ __init__.py  
|   |---♦ Accounts.py  
|   |---♦ cryption_tools.py  
|   |---♦ err_classes.py  
|   |---♦ FanController.py  
|   |---♦ ServerFuncs.py  
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
The **KeyFile.enc** is the default key if the client hasen't yet authentificated or to send errors. It is encrypted with the cryption_tools.low class.
**KingLog.json** is the file where all the Gaykings are saved (basically a *log*):
```Python
{
    "00.00.0000": "jesus",
    "30.05.2021": "John",
    "31.05.2021": "Will|John|Jack",
    "01.06.2021": "Jack",
}
```
The file **now.json** is used to save all current Votes (in case of a server restart/poweroff) and in newer versions generally used as the *Votes* Variable. It stores informations like this:
```Python
{
    "GayKing":
    {
        "Will": "Trains",
        "John": "Will"
    },
    "BestBusDriver":
    {
        "Tobi"
    }
}
```
**tempData.json** is used to transrer temperature data between the main program and the CPUHeatHandler:
```Python
{"temp": 29.0, "cptemp": 38.628, "hum": 39.0}
```
In **users.enc** is a fridrichcryption_tools.low encrypted dictionary with all users and passwords (low encryption because of speed)<br><br>
The **Version** file stores information about the current version: *Version:0.3.7,MaxLen:20* (Managed by the GUI developer).<br><br>
**yes.json** is basically the same file as *now.json* but from yesterday.<br><br>
All the files in the **moduels** folder are all just modules for the Server to run.<br><br><br>

## Fridrich Backend
The Backend File is meant to be imported by another programm (**Fridrich Dashboard**). It is generally used to communicate with the server, get informations and send votes.
The File Layout is straight forward:  
<pre>
|  
|---♦ data  
|   |---♦ KeyFile.enc  
|  
|---♦ modules  
|   |---♦ __init__.py  
|   |---♦ cryption_tools.py  
|   |---♦ err_classes.py  
|   |---♦ backend.py
|   |---♦ useful.py
|  
|---♦ YourProgramm.py  
</pre>  
Optionally there also is the file **FridrichBackendOffline.py** wich is for testing in case you can't connect to a Fridrich Server.
<br><br>
## Fridrich Dashboard
As you may have noticed, this program is not acutally included in this repository. The Programer of it has made his own repository, but the code is not open-source and he only publishes .exe files of his program (I really don't know why). So sadly, you either have to use the .exe or create your own program.