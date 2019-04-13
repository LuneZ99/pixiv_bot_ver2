import requests
from bs4 import BeautifulSoup
import json
import shutil
from PIL import Image
from io import BytesIO
import os
import time


class PixivError(Exception):
    """Pixiv API exception"""

    def __init__(self, reason, header=None, body=None):
        self.reason = str(reason)
        self.header = header
        self.body = body
        super(Exception, self).__init__(self, reason)

    def __str__(self):
        return self.reason


class JsonDict(dict):
    """general json object that allows attributes to be bound to and also behaves like a dict"""

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(r"'JsonDict' object has no attribute '%s'" % attr)

    def __setattr__(self, attr, value):
        self[attr] = value


class PixivAPI():

    # 别问我 我也不知道这两行是啥
    client_id = 'MOBrBDS8blbauoSck0ZfDbtuzpyT'
    client_secret = 'lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj'

    # 登陆状态储存
    access_token = None
    user_id = 0
    refresh_token = None


    def __init__(self, **requests_kwargs):
        """initialize requests kwargs if need be"""
        self.requests = requests.Session()
        self.requests_kwargs = requests_kwargs

    def parse_json(self, json_str):
        """parse str into JsonDict"""

        def _obj_hook(pairs):
            """convert json object to python object"""
            o = JsonDict()
            for k, v in pairs.items():
                o[str(k)] = v
            return o

        return json.loads(json_str, object_hook=_obj_hook)

    def require_auth(self):
        if self.access_token is None:
            raise PixivError('Authentication required! Call login() or set_auth() first!')

    def requests_call(self, method, url, headers={}, params=None, data=None, stream=False):
        """ requests http/https call for Pixiv API """
        try:
            if (method == 'GET'):
                return self.requests.get(url, params=params, headers=headers, stream=stream, **self.requests_kwargs)
            elif (method == 'POST'):
                return self.requests.post(url, params=params, data=data, headers=headers, stream=stream, **self.requests_kwargs)
            elif (method == 'DELETE'):
                return self.requests.delete(url, params=params, data=data, headers=headers, stream=stream, **self.requests_kwargs)
        except Exception as e:
            raise PixivError('requests %s %s error: %s' % (method, url, e))

        raise PixivError('Unknow method: %s' % method)

    def login(self, username, password):
        return self.auth(username=username, password=password)

    def auth(self, username=None, password=None, refresh_token=None):
        """Login with password, or use the refresh_token to acquire a new bearer token"""
        
        url = 'https://oauth.secure.pixiv.net/auth/token'
        headers = {
            'User-Agent': 'PixivAndroidApp/5.0.64 (Android 6.0)',
        }
        data = {
            'get_secure_url': 1,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

        if (username is not None) and (password is not None):
            data['grant_type'] = 'password'
            data['username'] = username
            data['password'] = password
        elif (refresh_token is not None) or (self.refresh_token is not None):
            data['grant_type'] = 'refresh_token'
            data['refresh_token'] = refresh_token or self.refresh_token
        else:
            raise PixivError('[ERROR] auth() but no password or refresh_token is set.')

        r = self.requests_call('POST', url, headers=headers, data=data)
        if (r.status_code not in [200, 301, 302]):
            if data['grant_type'] == 'password':
                raise PixivError('[ERROR] auth() failed! check username and password.\nHTTP %s: %s' % (r.status_code, r.text), header=r.headers, body=r.text)
            else:
                raise PixivError('[ERROR] auth() failed! check refresh_token.\nHTTP %s: %s' % (r.status_code, r.text), header=r.headers, body=r.text)

        token = None
        try:
            # get access_token
            token = self.parse_json(r.text)
            self.access_token = token.response.access_token
            self.user_id = token.response.user.id
            self.refresh_token = token.response.refresh_token
        except:
            raise PixivError('Get access_token error! Response: %s' % (token), header=r.headers, body=r.text)

        # return auth/token response
        return token


    """正式功能分割线"""

    def no_auth_requests_call(self, method, url, headers={}, params=None, data=None, req_auth=True):
        headers = { 'Referer': 'https://app-api.pixiv.net/' }
        if headers.get('User-Agent', None) == None and headers.get('user-agent', None) == None:
            # Set User-Agent if not provided
            headers['App-OS'] = 'ios'
            headers['App-OS-Version'] = '10.3.1'
            headers['App-Version'] = '6.7.1'
            headers['User-Agent'] = 'PixivIOSApp/6.7.1 (iOS 10.3.1; iPhone8,1)'
        if (not req_auth):
            return self.requests_call(method, url, headers, params, data)
        else:
            self.require_auth()
            headers['Authorization'] = 'Bearer %s' % self.access_token

            return self.requests_call(method, url, headers, params, data)

    def search_illust(self, word, mode='tag', order='desc', period='all',
            page=1, per_page=30,  req_auth=True):
        url = 'https://api.imjad.cn/pixiv/v1/'
        params = {
            'type': 'search',
            'word': word,
            'mode': mode,
            'order': order,
            'period': period,
            'page': page,
            'per_page': per_page,
        }

        r = self.no_auth_requests_call('GET', url, params=params, req_auth=req_auth)
        return r.text

    def download(self, url, prefix='', path=os.path.curdir, name=None, replace=False, referer='https://app-api.pixiv.net/'):
        """Download image to file (use 6.0 app-api)"""
        if not name:
            name = prefix + os.path.basename(url)
        else:
            name = prefix + name

        img_path = os.path.join(path, name)
        if (not os.path.exists(img_path)) or replace:
            # Write stream to file
            response = self.requests_call('GET', url, headers={ 'Referer': referer }, stream=True)
            with open(img_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response


    def search_download_all(self, word, name, mode='tag', order='desc', period='all',
            page=1, per_page=30):
        
        tag_json = []
        i = 0

        rt = self.search_illust(word, mode, order, period, page, per_page)
        rj = json.loads(rt)
        
        for l in range(0, len(rj['response'])):
            try:
                illust = rj['response'][l]
                print('{:0>4}'.format(str(i)), illust['tags'])
                tag_json.append(illust['tags'])
                url = illust['image_urls']['px_480mw']
                self.download(url=url, path='I:/pixiv/'+name+'/', name=name+'_'+'{:0>4}'.format(str(i))+'.jpg')
                i += 1
            except PixivError:
                print('访问被拒绝')
                time.sleep(10)
                continue
            
        return tag_json
    
_USERNAME = "corgiclub@yeah.net"
_PASSWORD = "corgiclubADMIN"

a = PixivAPI()
a.login(_USERNAME, _PASSWORD)
print('hello world!')
fi = open('characters0.json', encoding='utf-8')
cha = json.load(fi)
for i in cha:
    print(i)
    path = 'I:/pixiv/'+i[1]
    if not os.path.exists(path):
        os.makedirs(path)
    rr = a.search_download_all(word=i[0], name=i[1], per_page=7000)
    with open('I:/pixiv/'+i[1]+'/'+i[1]+'.json', 'w', encoding="utf8") as fi:
        json.dump(rr, fi, ensure_ascii=False, indent=4)
    print(i[1], 'done.')
