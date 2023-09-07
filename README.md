Scheduler for Students Bot in Telegram
========================================

Build sked container
--------------------

Use podman/docker to build sked-container image  
~~~shell
sudo podman build .
~~~

Deploy system locally
---------------------

Copy .env.example to .env and fill in the variables 

Then create creds.json file with instructions from [GoogleDevelopers](https://developers.google.com/sheets/api/quickstart/python)

~~~shell
sudo podman-compose up -d
~~~
