
# KotakeeOS - Home Management System

Home-brewed smart home management software; home assistant platform. Mean to
be hosted on a home local network (not exposed to the internet) as a
centralized control panel. A platform with immense potential for personal
AI/ML solution development. 

For more information, please see [Hobby Automation](http://hobbyautomation.com/).

![KotakeeOS Diagram](https://i.imgur.com/wb1CFzl.png "KotakeeOS Diagram")

![KotakeeOS Diagram](https://i.imgur.com/m3n26FX.png "KotakeeOS Diagram")

---

### Prerequisites

1. Python3 must be installed - version 3.8.X
2. Node.js must be installed. (with appropriate dependencies)
3. Speech Recognition - PyAudio and Speech Recognition modules are required.
4. AI/ML - specific modules must be installed. Utilize requirements.txt file 
   found within ./triggerWordDetection. Tensorflow 2.X required.
5. PocketSphinx speech detection - appropriate dependencies are required.

Note that, on mac,
you might need to update your xcode command line tools. If you have issues
with that, reference the following to delete and redownload xcode tools:

https://stackoverflow.com/questions/34617452/how-to-update-xcode-from-command-line

---

### Setup - Web Application (webApp)

1) Navigate inside of software directory
2) Execute "npm install"
3) Execute "npm start"

---

### Setup - Home Automation Microcontroller Modules

The KotakeeOS system architecture manipulates "actions" that may take place 
within various "rooms" of a home. Each action is associated with specific
interactions between Arduino microcontrollers and assorted components. These
actions may be associated with one or more pins. 

![KotakeeOS Diagram](https://i.imgur.com/G04JNw6.png "KotakeeOS Diagram")

In order to implement smart home capability with KotakeeOS, desired actions 
must first be decided upon, allocated to specific rooms. All actions will thus
be associated with a specific actionId as well as a roomId. The allocation of
actionIds to modules is dependent wholly on the installation location
of the microcontrollers and may be considered transparent to clients. For 
example, a room might have three lights controlled by three different modules,
or the room might have three lights controlled by a single module. For all
intents and purposes on the side of clients, the actions taken to manipulate 
these lights would be the same in either case.

Install modules in the appropriate locations with regards to the decided
methodology. For each module, ensure that the kotakeeosModule firmware is 
properly loaded. The IP Address is the only identifier for the server allowing
it to differentiate between modules, so it is crucial that all modules have
DCHP reservations provided. For each installed module, the server must, upon 
initialization, communicate what actionIds a module is responsible for, 
alongside the required pinout identifiers for each. 

Note that the code on each individual module, regardless of what implemented
actions are present, is exactly the same across all modules (referred to as
the module "firmware"). It is the server that prescribes action identifiers
and pinouts subsequently instigating specific behavior. 

Module data input may be supported via modules as well, provided to modules
in the same manner as actionsIds. Handling actions by the server must be 
defined accordingly. Examples of such definitions include turning on lights
given motion sensor input, activating a bathroom fan given a closed door, 
and activating the air conditioner given a specific thermometer reading. 

When developing further functionality, care should be taken in order to
maintain the existing server-centric design of the system architecture
in the future.

---

### Development Notes:

Transpilied Typescript has been set up to run whenever npm start is run. To 
avoid automatic transpiling (nothing changed), just run "node server.js"
instead of npm start. To transpile only (i.e. server is already running), 
use the following command in the software directory level:

node_modules/.bin/webpack ./public/static/libs/app.tsx --config webpack-config.js

To run only, use the following command:

node server.js

When working on the server (starting it over and over again) on a machine that
is not the active web server, make sure to provide an argument to stop the
server from providing real API data through any of the following methods:

node server.js feoijafeiof (any argument will do.)

npm run-script debug (also executes webpack like npm start)

---

For more information, please see [Hobby Automation](http://hobbyautomation.com/).

[![Hobby Automation Website](https://i.imgur.com/BMUoGOi.png "Hobby Automation Website")](http://hobbyautomation.com/)
