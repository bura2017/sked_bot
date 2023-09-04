FROM docker.io/library/python:3.11.5

COPY skedbot /
WORKDIR /skedbot
#COPY vars.py /
#COPY gsheet.py /


RUN pip install pyTelegramBotAPI
RUN pip install psycopg2
RUN pip install redis
RUN pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
RUN pip install python-dateutil


ENV WAIT_VERSION 2.7.2
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait /wait
RUN chmod +x /wait

#CMD ["python", "bot.py"]
CMD ["python", "skedbot/main.py"]
