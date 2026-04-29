FROM python:3-alpine

WORKDIR /app

RUN pip install Flask

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
