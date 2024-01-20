FROM python:alpine

RUN pip install pymodbus paho-mqtt

ADD main.py .

CMD python main.py
