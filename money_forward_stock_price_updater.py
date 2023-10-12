import datetime
import time
import re
import logging

import chromedriver_binary  # noqa
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from fake_useragent import UserAgent

from stock_price import get_current_price

logger = logging.getLogger(__name__)
rgx = re.compile(r'#(?P<comment>\w+)-(?P<code>\w+)-(?P<num>\d+)')


class MoneyForwardDriver(object):

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit()

    def __init__(self, headless=False):
        logger.debug(f'start. headless: {headless}')
        self.headless = headless
        options = webdriver.ChromeOptions()

        if self.headless:
            ua = UserAgent()
            user_agent = ua.random
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1280x1696")
            options.add_argument("--disable-application-cache")
            options.add_argument("--disable-infobars")
            options.add_argument("--no-sandbox")
            options.add_argument("--hide-scrollbars")
            options.add_argument("--lang=ja-JP")
            options.add_argument("--blink-settings=imagesEnabled=false")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--homedir=/tmp")
            options.add_argument(f'--user-agent={user_agent}')
            options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome(options=options)
        self._wait = WebDriverWait(self.driver, 15)
        self.driver.implicitly_wait(15)
        logger.debug('done.')

    def quit(self):
        if not self.headless:
            time.sleep(30)
        self.driver.quit()

    def get(self, url):
        logger.debug(f'start. url: {url}')
        self.driver.get(url)
        self.wait()
        logger.debug('done.')

    def get_current_url(self):
        return self.driver.current_url

    def check_url(self, expected_url):
        logger.debug(f'start. expected_url: {expected_url}')
        if not expected_url.endswith('/'):
            expected_url += '/'
        actual_url = self.get_current_url()
        if not actual_url.endswith('/'):
            actual_url += '/'
        assert actual_url == expected_url,\
            f'expected_url: {expected_url}, actual_url: {actual_url}'
        logger.debug('done.')

    def wait(self, locator=None, visible=True):
        if locator is None:
            self._wait.until(EC.presence_of_all_elements_located)
        elif visible:
            self._wait.until(EC.visibility_of_element_located(locator))
        else:
            self._wait.until_not(EC.visibility_of_element_located(locator))

    def find_element_by_css_selector(self, css_selector):
        return self.driver.find_element(by=By.CSS_SELECTOR, value=css_selector)

    def find_elements_by_css_selector(self, css_selector):
        return self.driver.find_elements(
            by=By.CSS_SELECTOR, value=css_selector)

    def click_unclickable_element(self, element):
        """
        click unclickable element
        https://stackoverflow.com/questions/37879010/selenium-debugging-element-is-not-clickable-at-point-x-y
        """
        self.driver.execute_script("arguments[0].click();", element)

    def update_value(self, element, value):
        element.clear()
        element.send_keys(value)

    def sign_in(self, mf_username, mf_pass):
        self.get('https://moneyforward.com')
        self.wait()

        logger.debug('click login')
        self.click_unclickable_element(
            self.find_element_by_css_selector('.web-sign-in > a'))
        self.wait()

        logger.debug(f'start. mf_username: {mf_username}')
        self.find_element_by_css_selector(
            'input[name="mfid_user[email]"]').send_keys(mf_username)
        logger.debug('username')
        self.find_element_by_css_selector('#submitto').click()
        logger.debug('submit')
        self.wait()

        time.sleep(3)
        self.find_element_by_css_selector(
            'input[name="mfid_user[password]"]').send_keys(mf_pass)
        logger.debug('password')
        self.find_element_by_css_selector('#submitto').click()
        logger.debug('submit 2')
        self.wait()

        time.sleep(3)
        logger.debug('skip biometric authentication')
        self.click_unclickable_element(
            self.find_element_by_css_selector('a[href^="/passkey_promotion/finalize_passkey_setup"]:not(#submitto)'))
        self.wait()

        url = self.get_current_url()
        if not url.endswith('/'):
            url += '/'
        if url == 'https://id.moneyforward.com/':
            self.get('https://moneyforward.com')
            self.wait()

            logger.debug('click login')
            self.click_unclickable_element(
                self.find_element_by_css_selector('.web-sign-in > a'))
            self.wait()

            logger.debug('click use this account')
            self.find_element_by_css_selector('#submitto').click()
            self.wait()

        self.check_url('https://moneyforward.com')
        logger.debug('done.')


def update(args):
    logger.debug('start.')
    with MoneyForwardDriver(headless=args.headless) as mf:
        mf.sign_in(args.mf_username, args.mf_pass)

        mf.get('https://moneyforward.com/bs/portfolio')
        mf.check_url('https://moneyforward.com/bs/portfolio')

        trs = mf.find_elements_by_css_selector(
            '#portfolio_det_eq > table.table-eq > tbody > tr')
        logger.debug(f'trs: {len(trs)}')

        for i in range(len(trs)):
            logger.debug(f'loop {i}: start.')
            # modal 表示後参照できなくなるため再取得
            trs = mf.find_elements_by_css_selector(
                '#portfolio_det_eq > table.table-eq > tbody > tr')
            tds = trs[i].find_elements(By.TAG_NAME, 'td')
            # 1: 銘柄名
            name = tds[1].text
            logger.debug(f'loop {i}: name: {name}')
            m = rgx.match(name)
            if m:
                logger.debug(f'loop {i}: match')
                code = m.group('code')
                num = int(m.group('num'))
                logger.debug(f'loop {i}: code: {code}, num: {num}')

                logger.debug(f'loop {i}: edit')
                # 11: 変更ボタン (modal 含む)
                mf.click_unclickable_element(
                    tds[11].find_element(By.TAG_NAME, 'a'))
                mf.wait()

                logger.debug(f'loop {i}: get_current_price')
                price = get_current_price(
                    code, 'USD', num,
                    datetime.datetime.now(
                        datetime.timezone(datetime.timedelta(hours=9))
                    ) - datetime.timedelta(days=1))
                logger.debug(f'loop {i}: price: {price}')

                mf.update_value(
                    tds[11].find_element(By.ID, 'user_asset_det_value'),
                    price)
                logger.debug(f'loop {i}: price: updated')

                entried_price = tds[11].find_element(
                    By.ID, 'user_asset_det_entried_price')
                entried_price_value = entried_price.get_attribute('value')
                logger.debug(
                    f'loop {i}: entried_price_value: {entried_price_value}')

                # 初期値が 0 の場合は取得日の評価額に更新
                if not entried_price_value or int(entried_price_value) == 0:
                    logger.debug(f'loop {i}: update entried_price_value')

                    entried_at = tds[11].find_element(
                        By.ID, 'user_asset_det_entried_at'
                    ).get_attribute('value')

                    logger.debug(f'loop {i}: entried_at: {entried_at}')
                    price_ent = get_current_price(
                        code, 'USD', num,
                        datetime.datetime.strptime(
                            entried_at + '+JST', '%Y/%m/%d+%Z'))
                    logger.debug(f'loop {i}: price_ent: {price_ent}')

                    mf.update_value(
                        entried_price,
                        price_ent)
                    logger.debug(f'loop {i}: price_ent: updated')

                logger.debug(f'loop {i}: save start.')
                tds[11].find_element(
                    By.CSS_SELECTOR, 'input[type=submit]').click()
                logger.debug(f'loop {i}: save done.')
            else:
                logger.debug(f'loop {i}: does not match')

            mf.wait(locator=(By.CSS_SELECTOR, 'input[type=submit]'),
                    visible=False)
            logger.debug(f'loop {i}: done.')
    logger.debug('done.')


if __name__ == '__main__':
    import argparse
    from utils import setup_logger

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--mf_username',
        type=str,
        required=True)

    argparser.add_argument(
        '--mf_pass',
        type=str,
        required=True)

    argparser.add_argument(
        '--headless',
        action='store_true')

    args = argparser.parse_args()

    for name in (__name__, 'stock_price'):
        logger = logging.getLogger(name)
        setup_logger(logger)

    update(args)
