FROM pypy:3.8
COPY ./server /app/server
EXPOSE 7777
CMD pypy /app/server/server.py
