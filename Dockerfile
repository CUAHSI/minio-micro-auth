FROM python:3.9

WORKDIR /app

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./api /app/api

ENV PYTHONPATH "${PYTHONPATH}:/"

RUN curl https://dl.min.io/client/mc/release/linux-arm64/mc -o /usr/local/bin/mc
RUN chmod +x /usr/local/bin/mc

CMD ["fastapi", "run", "api/main.py", "--port", "80", "--workers", "8"]
