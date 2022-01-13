FROM python:3.8

LABEL maintainer='Pavel Zakharov <pzakharov83@gmail.com>'

WORKDIR /code

COPY requirements.txt .

RUN python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . .

EXPOSE 8080

CMD ["python3", "server.py"] 
