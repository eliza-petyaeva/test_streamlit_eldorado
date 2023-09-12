# app/Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt

EXPOSE 8502

ENTRYPOINT ["streamlit", "run", "--server.port=8502"]

CMD ["app.py"]