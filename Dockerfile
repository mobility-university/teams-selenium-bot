FROM python3.8 # TODO: replace it with your image that should be used for the Bot

ENV DISPLAY=:99

RUN apt update && apt install -y ca-certificates wget unzip curl \
 && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
 && apt-get -y update \
 && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y google-chrome-stable \
 && wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip \
 && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
 && rm /tmp/chromedriver.zip \
 && pip install selenium==4.9.0 webdriver_manager

WORKDIR /bot
COPY bot.py bot.py
CMD ["./bot.py", "self-check"]
