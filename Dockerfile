FROM python:3.8

RUN mkdir -p /usr/src/bot/

WORKDIR /usr/src/bot/

COPY . /usr/src/bot/
RUN chmod +x wait-for-it.sh
RUN pip install --no-cache-dir -r requirements.txt

CMD ["./wait-for-it.sh", "dbpostgres:5432", "--", "python", "-u", "src/bot.py"]