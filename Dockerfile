FROM python:3.8

RUN mkdir -p /usr/src/bot/

WORKDIR /usr/src/bot/

COPY . /usr/src/bot/
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-u", "src/bot.py"]