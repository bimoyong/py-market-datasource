FROM python:3.10.12 AS build

ARG GIT_SSH_KEY \
    PORT

ENV HOST 0.0.0.0
ENV PORT $PORT

ADD . /app

RUN cd app && \
    GIT_SSH_KEY=$GIT_SSH_KEY pip install -r requirements.txt && \
    cd ..

WORKDIR /app

EXPOSE $PORT

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
