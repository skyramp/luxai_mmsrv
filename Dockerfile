FROM python:3.9
COPY ./server /app/server
EXPOSE 7777
CMD python /app/server/server.py