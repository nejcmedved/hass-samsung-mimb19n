FROM python:alpine

RUN pip install paho-mqtt

ADD main.py .

CMD python main.py
