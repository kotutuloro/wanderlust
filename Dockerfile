FROM python:3.13

WORKDIR /app

RUN pip install pipenv

COPY Pipfile Pipfile.lock ./

RUN pipenv install -d --system --deploy

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
