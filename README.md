# Fridrich
Fridrich is a project by 3 stupid guys who were bored so they created a Programm on wich they can vote whom of them is the gayest.
It mainly consits of three parts:
* Fridrich Server
* Fridrich Backend
* Fridrich Dashboard

## Fridrich Server
The Server is run on a Raspberry-Pi model 3b+ connected to the local network. It saves alle the data in files and accepts requests, handels events like the 0 o'clock vote and some other "cool" stuff. The basic File Layout for the Server should look like this:  
|  
|---♦ data  
|$~~~$|---♦ KeyFile.enc  
|  
|---♦ modules  
|$~~~$|---♦ __init__.py  
|$~~~$|---♦ Accounts.py  
|$~~~$|---♦ cryption_tools.py  
|$~~~$|---♦ err_classes.py  
|$~~~$|---♦ FanController.py  
|$~~~$|---♦ ServerFuncs.py  
|$~~~$|---♦ useful.py  
|  
|---♦ FridrichServer.py  
  
The **KeyFile.enc** is the default key if the client hasen't yet authentificated or to send errors. It is encrypted with the cryption_tools.low class. All the files in the **moduels** folder are all just modules for the Server to run.

## Fridrich Backend
The Backend File is actually ment to be imported by another programm (**Fridrich Dashboard**). It is generally used to communicate with the server, get informations and send votes.
The File Layout is pretty straight forward:  
|  
|---♦ modules  
|$~~~$|---♦ __init__.py  
|$~~~$|---♦ cryption_tools.py  
|$~~~$|---♦ err_classes.py  
|$~~~$|---♦ FridrichBackend.py  
|$~~~$|---♦ ServerFuncs.py  
|  
|---♦ YourProgramm.py  
  
## Fridrich Dashboard
As you may have noticed, this program is not acutally included in this repository. The Programer of it has made his own repository, but the code is not open-source and he only publishes .exe files of his program (I really don't know why). So sadly, you either have to use the .exe or create your own program.