FROM python:alpine

RUN pip install paho-mqtt python-dotenv

ADD main.py .
ADD mqtt_config.py .
ADD cmd_shell.py .
ADD samsung_nasa samsung_nasa

CMD python main.py
