import datetime
from decimal import Decimal, ROUND_HALF_UP
import logging

import share

logger = logging.getLogger(__name__)


class DataNotFoundException(Exception):
    pass


def round(f, precision=2):
    return Decimal(str(f)).quantize(
            Decimal(str(10 ** -precision)), rounding=ROUND_HALF_UP)


def get_last_close(code, base_date, retry=0):
    """
    終値を取得する
    https://support.yahoo-net.jp/PccFinance/s/article/H000006613
    米国株: 現地時間の 16:00 が終値に相当
    ニューヨーク: 16:00 EDT (UTC-4) => 20:00 UTC
    """
    stock = share.Share(code)

    try:
        if code.endswith('=X'):
            symbol_data = stock.get_historical_with_base_date(
                share.PERIOD_TYPE_DAY, 1,
                share.FREQUENCY_TYPE_HOUR, 1, base_date)

            if symbol_data is None:
                raise DataNotFoundException
            for timestamp, close in zip(
                    symbol_data['timestamp'], symbol_data['close']):
                dt = datetime.datetime.fromtimestamp(
                    int(timestamp) / 1000, tz=datetime.timezone.utc)
                if dt.hour == 20:  # 20:00 UTC
                    last_close = close
                    break
            else:
                raise DataNotFoundException
        else:
            symbol_data = stock.get_historical_with_base_date(
                share.PERIOD_TYPE_DAY, 1,
                share.FREQUENCY_TYPE_DAY, 1, base_date)

            if symbol_data is None:
                raise DataNotFoundException
            else:
                last_close = symbol_data['close'][0]

        return round(last_close)
    except DataNotFoundException:
        if retry > 5:
            logger.error(
                f'{code} data is not found: {base_date:%Y-%m-%d}, '
                f'retry x{retry}, stopped.')
            raise

        logger.debug(
            f'{code} data is not found: {base_date:%Y-%m-%d}, retry x{retry}.')

        return get_last_close(
            code, base_date - datetime.timedelta(days=1), retry + 1)


def get_current_price(code, currency, shares, date):
    """
    code: 証券コード
    currency: 株式の通貨単位
    shares: 株数
    """
    logger.debug(
        f'code: {code}, currency: {currency}, '
        f'shares: {shares}, date: {date:%Y-%m-%d}')

    base_date = date + datetime.timedelta(days=1)
    price = get_last_close(code, base_date)

    if currency != 'JPY':
        rate = get_last_close(f'{currency}JPY=X', base_date)
    else:
        rate = round(1)

    current_price = int(round(price * rate, 0)) * shares

    logger.debug(
        f'price: {price}, rate: {rate}, shares: {shares}, '
        f'current_price: {current_price}')

    return current_price


if __name__ == '__main__':
    """
    $ python stock_price.py --code AMZN --currency USD \
            --shares 2 --date 2022-04-15
    763812
    """
    import argparse
    from utils import setup_logger

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--code',
        type=str,
        required=True)

    parser.add_argument(
        '--currency',
        type=str,
        default='USD')

    parser.add_argument(
        '--shares',
        type=int,
        default=1)

    parser.add_argument(
        '--date',
        type=lambda s: datetime.datetime.strptime(s + '+JST', '%Y-%m-%d+%Z'),
        default=datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ) - datetime.timedelta(days=1))

    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    setup_logger(logger)
    print(get_current_price(args.code, args.currency, args.shares, args.date))
