FROM docker.io/library/python:3.11.5

COPY requirements.txt /
RUN pip install -r requirements.txt

ENV WAIT_VERSION 2.7.2
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait /wait
RUN chmod +x /wait

COPY skedbot /skedbot
WORKDIR /
ENV PYTHONPATH=/

CMD ["python", "skedbot/main.py"]
