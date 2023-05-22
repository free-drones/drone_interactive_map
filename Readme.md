# Drone Interactive Map
This is the Drone Interactive Map application. More info to come!

# Credits
The concept is developed by Andreas Gising as an attempt to go straight from consumption of collected information to control of a system of systems.
The implementation is mainly done by very intelligent and ambitious students from Linköping University. Through the PUM course (ProgramUtvecklingsMetodik), a course where the students meet realistic challenges and customer relations, student groups have run a development project with RISE as customer.
One group of 7 started in 2020, see [their report here](http://www.diva-portal.org/smash/record.jsf?pid=diva2:1444831).
Another group of 10 started in 2023, their work is ongoing.

Main contributors from RISE are, Andreas Gising, Lennart Ochel, Rasmus Lundqvist and Kristoffer Bergman.

# Starting the application

Via RISE server 
Start Dronelink
1. Open VPN to RISE server
2. SSH to the server: ssh pum01-23@10.44.170.10
3. Change folder:  cd rise_drones/src/app/
4. Start Dronelink : python app_drone_link.py

Start simulated drones
5. Navigated to the website c2m2 : URL "10.44.170.10" 
6. Start simulated drones:  Click / -> tasks -> / -> start SITL+DSS (Either 1 or 3)

Start Backend
7.1. Create a virtual environment: python -m venv venv
7.2. Start the virtual environment: venv\scripts\Activate.ps1
7.3. Install all requirements : pip install -r .\requirements.txt
8. Start backend with RDS : python .\run_RDS_and_IMM.py or python3 .\run_RDS_and_IMM.py
8.1 Start backend without RDS : python .\IMM_app.py or python3 .\IMM_app.py

Configure drones
9. Start QGroundcontrol
9.1 (If first time) - Set "Firmware" to Ardupilot and "Typ" to Multirotor
10. Click on the top left logo -> application settings -> Comm Links -> Add
11. For each drone that will be added: Name: arbitrarily, Type: TCP, Server Address: 10.44.170.10
12. Port: [17781, 17783 or 17785] depending on the amount of drones (if you start 3). 17787 if you start 1.
If this does not work the port can be found under the mavproxy.py process in c2m2 (one row per drone). Use the "free" port (The one which is not used in the corresponding DSS).
13. After the drone is created click on "yourdronename" -> connect.
14. Return to the homescreen (top left).
15. Put the drone in Guided mode by clicking on "stabilize" then change it to guided.

Start Frontend
15. Change the "testing" flag to false in App.js under front-end/react-base/src/JS.
16. Navigate to React-base.
17. Start a terminal and write "npm start"
You can now access the website on "http://localhost:3000/StartUp"
18. If you want the application to be able to access your location (Chrome) you need to change the following flag: chrome://flags/#unsafely-treat-insecure-origin-as-secure