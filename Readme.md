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
Starta Dronelink
1. Open VPN till RISE server
2. SSH till server: ssh pum01-23@10.44.170.10
3. Byt folder:  cd rise_drones/src/app/
4. Starta Dronelink : python app_drone_link.py

Starta simulerade drönare
5. Navigera till hemsidan c2m2 : skriv "10.44.170.10" i webbläsaren
6. Starta simulerade drönare:  Klicka / -> tasks -> / -> start SITL+DSS (antingen 1 eller 3)
Starta Backend

7.1. Skapa virtual enviroment: python -m venv venv
7.2. Starta virtual enviroment: venv\scripts\Activate.ps1
7.3. Ladda ned alla requirements : pip install -r .\requirements.txt
8. Starta backend : python .\run_RDS_and_IMM.py eller python3 .\run_RDS_and_IMM.py

Konfigurera drönare
9. Starta QGroundcontrol
9.1 (Om första gången) - Sätt Firmware till Ardupilot och Typ till Multirotor
10. Klicka på loggan uppe till vänster -> application settings -> Comm Links -> Add
11. För varje drönare som ska läggas till: Name: godtyckligt, Type: TCP, Server Adress: 10.44.170.10
12. Port: [17781, 17783 eller 17785] beroende på drönarnummer (om man startar 3 st). 17787 om man startar 1.
Om detta inte funkar kan port hittas under mavproxy.py processen i c2m2 (en rad per drönare). Använd då den "lediga" porten (dvs den som inte används av motsvarande DSS process i raderna under).
13. Efter att drönaren är skapad. Klicka på "ditt drone name" -> connect.
14. Återvänd till startskärmen (back uppe till vänster)
15. Sätt drönaren i Guided mode genom att klicka på "stabilize" (eller liknande) uppe till vänster -> ändra till guided.

Starta Frontend
15. Ändra "Testing" till false i App.js under front-end/react-base/src/JS
16. Navigera till React-base i projectfoldern.
17. Starta terminal och skriv "npm start"
Nu borde hemsidan nås via "http://localhost:3000/StartUp"