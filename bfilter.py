import time
import json
from typing import Iterable
import requests
import pickle
import csv
from selenium import webdriver


class FilterController(object):
    def __init__(
        self,
        load_cookies: bool = False,
        session: requests.sessions.Session = requests.Session()
    ) -> None:
        super().__init__()
        self.session = session
        self.csrf_token = ''
        if load_cookies:
            self.load_cookies()

    def fetch_filters(self) -> None:
        filters_url = 'https://api.bilibili.com/x/dm/filter/user?jsonp=jsonp'
        response = self.session.get(filters_url)
        self.filters = json.loads(response.content.decode())

    def add(self, type, filter: str) -> dict:
        add_filter_url = 'https://api.bilibili.com/x/dm/filter/user/add'
        data = {
            'type': str(type),
            'filter': filter,
            'jsonp': 'jsonp',
            'csrf': self.csrf_token
        }
        response = self.session.post(add_filter_url, data=data)
        response_json = json.loads(response.content.decode())
        return response_json

    def delete(self, id) -> dict:
        delete_filter_url = 'https://api.bilibili.com/x/dm/filter/user/del'
        data = {'ids': str(id), 'jsonp': 'jsonp', 'csrf': self.csrf_token}
        response = self.session.post(delete_filter_url, data=data)
        response_json = json.loads(response.content.decode())
        return response_json

    def set_csrf(self) -> None:
        try:
            self.csrf_token = self.session.cookies.get('bili_jct')
            # print('[Debug] CSRF token set to \'{}\''.format(self.csrf_token))
        except Exception:
            print('[Error] Failed to set csrf token')

    def save_cookies(self, file: str = 'cookies.pkl') -> None:
        with open(file, 'wb') as f:
            pickle.dump(self.session.cookies, f)

    def load_cookies(self, file: str = 'cookies.pkl') -> None:
        with open(file, 'rb') as f:
            self.session.cookies.update(pickle.load(f))
        self.set_csrf()

    @staticmethod
    def load() -> 'FilterController':
        return FilterController(load_cookies=True)


class FilterManager(object):
    def __init__(self, controller: FilterController) -> None:
        super().__init__()
        self.controller = controller
        self.local_filters = []
        self.remote_filters = []
        self.fetch_filters()

    def fetch_filters(self) -> None:
        self.controller.fetch_filters()
        self.remote_filters = []
        for rule in self.controller.filters['data']['rule']:
            self.remote_filters.append(
                (str(rule['type']), str(rule['filter']), str(rule['id'])))

    def list_filters(self, remote=True) -> str:
        if remote:
            filters = self.remote_filters
            result = 'id\ttype\tfilter\n'
        else:
            filters = self.local_filters
            result = 'type\tfilter\n'
        for filter in filters:
            if remote:
                filter_line = '{}\t{}\t{}\n'.format(str(filter[2]),
                                                    str(filter[0]),
                                                    str(filter[1]))
            else:
                filter_line = '{}\t{}\n'.format(str(filter[0]), str(filter[1]))
            result += filter_line
        print(result)
        return result

    def upload_filters(self,
                       retry: int = 0,
                       interval: float = 0.5) -> Iterable[Iterable]:
        failed = self._upload_filters(self.local_filters, interval)
        while retry > 0 and len(failed) > 0:
            interval += 0.5
            failed = self._upload_filters(failed, interval=interval)
        return failed

    def _upload_filters(self,
                        filters: Iterable[Iterable],
                        interval: float = 0.5) -> Iterable[Iterable]:
        failed = []
        for filter in filters:
            response = self.controller.add(filter[0], filter[1])
            if response['code'] == 0:
                print('filter {}:{} uploaded'.format(str(filter[0]),
                                                     str(filter[1])))
            else:
                failed.append(filter)
                print('filter {}:{} upload failed'.format(
                    str(filter[0]), str(filter[1])))
            time.sleep(interval)
        self.fetch_filters()
        return failed

    def load_filters(self, file: str) -> None:
        self.local_filters = self._load_filters(file)

    def dump_filters(self,
                     file: str,
                     append: str = False,
                     remote: bool = False):
        filters = []
        if remote:
            for filter in self.remote_filters:
                filters.append((filter[0], filter[1]))
        else:
            filters = self.local_filters.copy()
        self._dump_filters(filters, file, append)

    @staticmethod
    def _load_filters(file: str) -> Iterable[Iterable]:
        filters = []
        with open(file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            reader.__next__()
            for row in reader:
                if len(row) >= 2:
                    filters.append((row[0], row[1]))
        return filters

    @staticmethod
    def _dump_filters(filters: Iterable[Iterable],
                      file: str,
                      append: bool = False):
        if append:
            mode = 'a'
        else:
            mode = 'w'
        f = open(file=file, mode=mode, encoding='utf-8', newline='')
        writer = csv.writer(f)
        if not append:
            writer.writerow(('type', 'filter'))
        writer.writerows(filters)
        f.close()


def set_cookies(cookies,
                ua: str = False,
                session: requests.sessions.Session = requests.Session()):
    if ua != False:
        session.headers.update({"user-agent": ua})
    for cookie in cookies:
        session.cookies.set(cookie['name'],
                            cookie['value'],
                            domain=cookie['domain'])
    return session


def selenium_login_firefox():
    print('Please login via the browser then come back.')
    print('DO NOT CLOSE THE BROWSER!!!')
    time.sleep(1)
    browser = webdriver.Firefox()
    browser.get('https://passport.bilibili.com/login')
    input('Press <Enter> to continue.')
    cookies = browser.get_cookies()
    browser.close()
    return cookies


def login() -> FilterController:
    cookies = selenium_login_firefox()
    session = set_cookies(cookies)
    fc = FilterController(session=session)
    # fc.save_cookies(file=file)
    return fc


if __name__ == '__main__':
    fc = FilterController.load()
    #fm.add('6')
    #fc = login()
    #fc.save_cookies()
    fm = FilterManager(fc)
    fm.list_filters()
    fm.load_filters('test.csv')
    fm.upload_filters()
    fm.list_filters()
