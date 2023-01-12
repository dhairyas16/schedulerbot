FROM python:3.9

RUN apt-get update

WORKDIR /app

COPY requirements.txt ./

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "3", "-b", ":5000", "-t", "360", "wsgi:app"]