# Fridrich
Fridrich is a project by 3 stupid guys who were bored, so they created a program on which they can vote who of them is the gayest. 
It mainly consists of three parts:
* Fridrich Server
* Fridrich Backend
* Fridrich Dashboard
<br><br><br>
# Fridrich Server
## Installation
### Step 1: Clone this repository
Clone this Repo to your target directory. ( [how to clone a github repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) )<br>
Then head to your directory:
```bash
cd /your/directory/Fridrich/
```

### Step 2: Install python 3.10 on your system
This step is going to be different for every OS. Here is an example for rasbian:
<br>
[python3.10 installation for raspberry-pi](https://raspberrytips.com/install-latest-python-raspberry-pi/)
<br>
### Step 3: Installing the python libraries (pip)
you can easily install the fridrich module and dependencies with pip:
```bash
pip install fridrich
```
if you install the package this way, you can delete the ```fridrich``` folder in your
directory
### Setp 3: Installing the python libraries (manual)
If you plan on using FridrichDiscordBot, edit *requirements.txt* and uncomment everything after **# only for FridrichDiscordBot**:
```bash
cryptography==3.3.2
numpy

# only for GayHistoryAnalyser
# matplotlib
# seaborn
# pandas

# only for FridrichDiscordBot
discord.py

```
The same thing applies for GayHistoryAnalyser.

In your Fridrich directory, run:

For Linux:
```bash
python3.10 -m pip install -r requirements.txt
```
For Windows:
```batch
pip3.10 -m pip install -r requirements.txt
```
### Step 4: create the required files
Copy the *data* directory from [this](https://www.github.com/Nilusink/FridrichServer-Docker/) repository
into your directory.
<br>
### Step 5: Adjust settings.json
The file *settings.json* can be found under **Fridrich/fridrich/server/** and contains
all the settings for the server. In this file there are other settings as well, but the
ones we need are those with filepaths in them.<br>
Then for every directory replace **/home/pi/Server/** with your directory.

Ex.:
```bash
"lastFile": "/home/pi/Server/data/yes.json"
```
to
```bash
"lastFile": "/your/server/directory/Fridrich/data/yes.json"
```

### Step 6 (optional): Autostart
If you want your server to run every time on startup, you can put FridrichServer (and FridrichDiscordBot)
into autostart. Again, this step is going to be different for every system, but
here is an example for rasbian:

Open the file with nano:
```bash
sudo nano /etc/rc.local
```
Add the following line to the end of the file (before *exit 0*):
```bash
python3 /path/do/your/server/FridrichServer.py &
```
And optionally:
```bash
python3 /path/do/your/server/FridrichDiscordBot.py &
```
## Description
The Server is run on a Raspberry-Pi model 3b+ connected to the local network. It saves all the data in files and accepts requests, handles events like the 0 o'clock vote and some other "cool" stuff.
<br><br><br>
The **Calendar.json** file saves the configurations of the calendar in a dict:
```json 
{'10.10.2005' : ['stuff happened', 'some other things happened as well'], '11.10.2005' : []}
```
**dVotes.json** stores all the data about how many double votes each user has left in this week:
```json
{"User1": 1, "User2": 0}
```
The **KeyFile.enc** is the default key if the client hasn't yet authenticated or sends errors. It is encrypted with the cryption_tools.low class.
**logs/*** are the files where all the voting results are stored (basically a *log*):
```json
{
    "00.00.0000": "jesus",
    "30.05.2021": "John",
    "31.05.2021": "Will|John|Jack",
    "01.06.2021": "Jack"
}
```
The file **now.json** is used to save all current Votes (in case of a server restart/power off) and in newer versions generally used as the *Votes* Variable. It stores information like this:
```json
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

In **users.enc** is a fridrich.cryption_tools.low encrypted dictionary with all users and passwords (low encryption because of speed)<br><br>
The **Version** file stores information about the current version: *Version:0.3.7,MaxLen:20* (Managed by the GUI developer).
**yes.json** is basically the same file as *now.json* but from yesterday.<br><br>
All the files in the **fridrich** folder are just modules for the Server to run.

## FridrichDiscordBot
To run the discord bot you must replace the *TOKEN*
with your discord bot's Token and the 
*CHANNEL_ID* with your discord servers channel id
<br>
*How?*
<br>
[Follow the steps in this tutorial](https://realpython.com/how-to-make-a-discord-bot-python/)
<br><br>
# Fridrich Backend
The Backend File is meant to be imported by another program (**Fridrich Dashboard**). It is generally used to communicate with the server, get information and send votes.
The File Layout is straightforward:  
<pre>
|  
|---♦ data  
|   |---♦ KeyFile.enc
|  
|---♦ fridrich
|   |---♦ backend
|   |   |---♦ __init_.py
|   |   |---♦ debugging.py
|   |
|   |---♦ __init__.py
|   |---♦ classes.py
|   |---♦ errors.py
|   |---♦ cryption_tools.py
|  
|---♦ YourProgram.py  
</pre>  
Optionally there also is the file **FridrichBackendOffline.py** which is for testing if you can't connect to a Fridrich Server.
<br><br>
# Fridrich Dashboard
As you may have noticed, this program is not actually included in this repository. The Programmer of it
doesn't want his code to be open-source, so unfortunately you have to make your own program.
As an example of how to use the fridrich module, you can use **VersionChanger.py**, **AppStore.py**
and **adminTool.py**.
<br><br>
# Installation with Docker
There are three docker-images available for Fridrich:

- **Server**: nilusink/fridrich_server
- **BackendAccessPanel**: nilusink/fridrich_backend_access

To run any of the above listed containers, you first need to [install Docker for your
system](https://docs.docker.com/get-docker/).

Then you need to *pull* the container you want to run.<br>Open a terminal and type:
<pre>
docker pull |name of container|:|container version|
</pre>
Instead of *container version*, you can also use *latest* to ensure you have the latest updates of the container.

example:
```bash
docker pull nilusink/fridrich_server:latest
```
To then *run* the container, type:
```bash
docker run --rm -it |name of container|:|container version|
```
For the server add 
```bash
-p 12345:12345
```
Before the docker name (so you can access the port the server uses)<br>
To look up the newest version for each container, follow [this](https://hub.docker.com/u/nilusink) link and click  on the desired repository.

example:
```bash
docker run --rm -it -p 12345:12345 nilusink/fridrich_server:latest
```

# **Attention!**
This project uses Python-3.10 Syntax (Server and backend), so it won't run on anything else than Python-3.10 or Higher!
