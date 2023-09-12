Scheduler for Students Bot in Telegram
========================================

Build sked container
--------------------

Use podman/docker to build sked-container image  
~~~shell
sudo podman build -t localhost/library/sked_bot:1.0 .
~~~
After successfull build you will see in the end
~~~
COMMIT localhost/library/sked_bot:1.0
--> af313230e99
Successfully tagged localhost/library/sked_bot:1.0
af313230e99b470452c2080dbea504da0db04146da5255d45b968b420b7a5363
~~~

Deploy system locally
---------------------

Copy .env.example to .env and fill in the variables 

Then create creds.json file with instructions from [GoogleDevelopers](https://developers.google.com/sheets/api/quickstart/python)

Create logs file: 
~~~shell
sudo touch /var/log/sked.log
~~~
Generate _token.pickle_ for Google Sheets access. Execute command and grant privileges to the application
~~~shell
python skedbot/gsheet.py
~~~
Launch podman compose
~~~shell
sudo podman-compose up -d
~~~

Enjoy logs in `/var/log/sked.log`


