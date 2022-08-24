import datetime

import requests
from yahoo_finance_api2.share import (
    Share as OriginShare,
    PERIOD_TYPE_DAY,
    PERIOD_TYPE_WEEK,
    PERIOD_TYPE_MONTH,
    PERIOD_TYPE_YEAR,
    FREQUENCY_TYPE_MINUTE,
    FREQUENCY_TYPE_HOUR,
    FREQUENCY_TYPE_DAY,
    FREQUENCY_TYPE_WEEK,
    FREQUENCY_TYPE_MONTH,
)


class Share(OriginShare):

    def get_historical_with_base_date(
                self, period_type, period,
                frequency_type, frequency, base_date):
        data = self._download_symbol_data_with_base_date(
            period_type, period, frequency_type, frequency, base_date)

        valid_frequency_types = [
            FREQUENCY_TYPE_MINUTE, FREQUENCY_TYPE_HOUR, FREQUENCY_TYPE_DAY,
            FREQUENCY_TYPE_WEEK, FREQUENCY_TYPE_MONTH
        ]

        if frequency_type not in valid_frequency_types:
            raise ValueError('Invalid frequency type: ' % frequency_type)

        if 'timestamp' not in data:
            return None

        return_data = {
            'timestamp': [x * 1000 for x in data['timestamp']],
            'open': data['indicators']['quote'][0]['open'],
            'high': data['indicators']['quote'][0]['high'],
            'low': data['indicators']['quote'][0]['low'],
            'close': data['indicators']['quote'][0]['close'],
            'volume': data['indicators']['quote'][0]['volume']
        }

        return return_data

    def _set_time_frame_with_base_date(self, period_type, period, base_date):
        if period_type == PERIOD_TYPE_DAY:
            period = min(period, 59)
            start_time = base_date - datetime.timedelta(days=period)
        elif period_type == PERIOD_TYPE_WEEK:
            period = min(period, 59)
            start_time = base_date - datetime.timedelta(days=period * 7)
        elif period_type == PERIOD_TYPE_MONTH:
            period = min(period, 59)
            start_time = base_date - datetime.timedelta(days=period * 30)
        elif period_type == PERIOD_TYPE_YEAR:
            period = min(period, 59)
            start_time = base_date - datetime.timedelta(days=period * 365)
        else:
            raise ValueError('Invalid period type: ' % period_type)

        end_time = base_date

        return int(start_time.timestamp()), int(end_time.timestamp())

    def _download_symbol_data_with_base_date(
                self, period_type, period,
                frequency_type, frequency, base_date):
        start_time, end_time = self._set_time_frame_with_base_date(
            period_type, period, base_date)
        url = (
            'https://query1.finance.yahoo.com/v8/finance/chart/{0}?symbol={0}'
            '&period1={1}&period2={2}&interval={3}&'
            'includePrePost=true&events=div%7Csplit%7Cearn&lang=en-US&'
            'region=US&crumb=t5QZMhgytYZ&corsDomain=finance.yahoo.com'
        ).format(self.symbol, start_time, end_time,
                 self._frequency_str(frequency_type, frequency))

        headers = {'User-Agent': ''}
        resp_json = requests.get(url, headers=headers).json()

        if self._is_yf_response_error(resp_json):
            self._raise_yf_response_error(resp_json)
            return

        data_json = resp_json['chart']['result'][0]

        return data_json
