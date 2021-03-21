import time
import json
import requests
import pickle
from selenium import webdriver

class FilterManager(object):
    def __init__(self, load_cookies:bool = False, session: requests.sessions.Session = requests.Session()) -> None:
        super().__init__()
        self.session = session
        self.csrf_token = ''
        if load_cookies:
            self.load_cookies()

    def load_filters(self) -> None:
        filters_url = 'https://api.bilibili.com/x/dm/filter/user?jsonp=jsonp'
        response = self.session.get(filters_url)
        self.filters = json.loads(response.content.decode())

    def add(self, filter: str) -> dict:
        add_filter_url = 'https://api.bilibili.com/x/dm/filter/user/add'
        data = {'type': '0', 'filter': filter, 'jsonp': 'jsonp', 'csrf': self.csrf_token}
        response = self.session.post(add_filter_url, data=data)
        response_json = json.loads(response.content.decode())
        return response_json

    def delete(self, id) -> dict:
        delete_filter_url = 'https://api.bilibili.com/x/dm/filter/user/del'
        data = {'ids': str(id), 'jsonp': 'jsonp','csrf': self.csrf_token}
        response = self.session.post(delete_filter_url, data=data)
        response_json = json.loads(response.content.decode())
        return response_json

    def set_csrf(self) -> None:
        try:
            self.csrf_token = self.session.cookies.get('bili_jct')
            print('[Debug] CSRF token set to \'{}\''.format(self.csrf_token))
        except Exception:
            print('[Error] Failed to set csrf token')

    def save_cookies(self) -> None:
        with open('cookies.pkl', 'wb') as f:
            pickle.dump(self.session.cookies, f)

    def load_cookies(self) -> None:
        with open('cookies.pkl', 'rb') as f:
            self.session.cookies.update(pickle.load(f))
        self.set_csrf()


def set_cookies(cookies, ua: str = False, session: requests.sessions.Session = requests.Session()):
    if ua != False:
        session.headers.update({"user-agent": ua})
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
    return session

def selenium_login_firefox():
    print('Please login via the browser then come back.\nDO NOT CLOSE THE BROWSER!!!')
    time.sleep(1)
    browser = webdriver.Firefox()
    browser.get('https://passport.bilibili.com/login')
    input('Press <Enter> to continue.')
    cookies = browser.get_cookies()
    browser.close()
    return cookies

def login() -> FilterManager:
    cookies = selenium_login_firefox()
    session = set_cookies(cookies)
    fm = FilterManager(session=session)
    fm.save_cookies()
    return fm

if __name__ == '__main__':
    fm = FilterManager(load_cookies=True)
    #fm.add('6')
    fm.load_filters()
    print(fm.filters)
