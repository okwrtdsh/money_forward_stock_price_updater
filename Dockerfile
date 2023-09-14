FROM python:3
WORKDIR /usr/src/app

RUN apt-get update -qq \
 && apt-get upgrade -y \
 && sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
 && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && apt-get update -qq \
 && apt-get install --no-install-recommends -y \
	google-chrome-stable \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN pip --no-cache-dir install \
	chromedriver-binary~=`google-chrome --version | sed -e 's/\([A-Za-z ]*\)\([0-9]*\.[0-9]*\).*/\2/g'` \
	selenium \
	yahoo-finance-api2 \
	fake-useragent

ENV MF_USERNAME=mf_username \
	MF_PASS=mf_pass

COPY money_forward_stock_price_updater.py .
COPY stock_price.py .
COPY share.py .
COPY utils.py .

CMD python money_forward_stock_price_updater.py --mf_username $MF_USERNAME --mf_pass $MF_PASS --headless
