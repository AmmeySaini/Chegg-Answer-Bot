import requests
import urllib3
import json
import base64
import time
import string
import random
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CheggHelper:
    def __init__(self):
        self.log_url = 'https://proxy.chegg.com/oidc/token'
        self.mfa_url = 'https://proxy.chegg.com/oidc/mfa'
        self.verify_mfa = 'https://proxy.chegg.com/oidc/token'
        self.getAns = 'https://proxy.chegg.com/mobile-study-bff/graphql/'
        self.tbs = 'https://proxy.chegg.com/v1/tbs/_/solution'
        self.heads = {
            'user-agent': 'CheggApp/3.39.0 (com.chegg.mobile.consumer; build:3.39.0.0; iOS 14.5.0) Alamofire/5.2.2',
            'authorization': 'Basic MFQxOE5HYmFsUURGYzBnWkh6b3ZwZVJkN0E1Y3BMQ3g6dnRnamFZa3Ric2p4OUFPUg==',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive'
        }

        self.web_heads = {
            'authority': 'www.chegg.com',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-US,en;q=0.9',
        }
    
    def try2FA(self, mfaToken, factors):
        for indd, i in enumerate(factors):
            print('[*] ' + str(indd + 1) + '. ' + i['channelType'] + ' ' + i['name'])
        print('[*] Enter Channel id to continue')
        idd = int(input())
        f_id = factors[idd - 1]['id']
        f_channel = factors[idd - 1]['channelType']
        data = {
            'factor_id': f_id,
            'mfa_token': mfaToken
        }
        
        res = requests.post(url=self.mfa_url, data=data, headers=self.heads, verify=False)
        js = res.json()
        if js['httpCode'] == 200:
            mfaEventId = js['mfaEventId']
            print('[*] OTP Sent')
            worked = False
            while worked != True:
                print('[*] Enter OTP: ', end='')
                otp_code = input()
                data2 = {
                    'mfa_event_id': mfaEventId,
                    'source_page': 'ios CheggApp 3.36.0|cs',
                    'source_product': 'ios|cs',
                    'mfa_code': otp_code,
                    'mfa_token': mfaToken,
                    'grant_type': 'mfa_code'
                }
                res2 = requests.post(url=self.verify_mfa, data=data2, headers=self.heads, verify=False)
                js1 = res2.json()
                if 'error' in res2.text:
                    print(js1['error'])
                elif js1['access_token'] != None:
                    worked = True
                    access_token = js1['access_token']
                    refresh_token = js1['refresh_token']
                    id_token = js1['id_token']
                    with open('settings.json', 'w') as fp:
                        data = {
                            'access_token': access_token,
                            'refresh_token': refresh_token,
                            'id_token': id_token
                        }
                        fp.write(json.dumps(data))
                    print('[*] Setup Completed')
                else:
                    print(res2.text)

        else:
            print(res.text)

    
    def getRefreshToken(self):
        with open('settings.json', 'r') as fp:
            js = json.loads(fp.read())
        data = {
            'source_page': 'ios CheggApp 3.36.0|cs',
            'source_product': 'ios|cs',
            'grant_type': 'refresh_token',
            'refresh_token': js['refresh_token']
        }

        res1 = requests.post(url=self.log_url, data=data, headers=self.heads, verify=False)
        js = res1.json()
        if 'access_token' in res1.text:
            if js['access_token'] != None:
                access_token = js['access_token']
                refresh_token = js['refresh_token']
                id_token = js['id_token']
                with open('settings.json', 'w') as fp:
                    data = {
                        'access_token': access_token,
                        'refresh_token': refresh_token,
                        'id_token': id_token
                    }
                    fp.write(json.dumps(data))
            elif 'error' in res1.text:
                print(js['error'])
        else:
            print(res1.text)

    def chkTokenValid(self, access_token):
        ex = access_token.split('.')[1] + '=='
        js = json.loads(base64.b64decode(ex))
        exp = js['exp']
        if exp > int(time.time()):
            return True
        else:
            return False
    
    def getQAns(self, ques_url):
        with open('settings.json', 'r') as fp:
            js = json.loads(fp.read())
        access_token = js['access_token']
        if self.chkTokenValid(access_token):
            pass
        else:
            self.getRefreshToken()
        
        return self.getQuesAns(ques_url)
    
    def getQuesAns(self, q_url):
        try:
            res = requests.get(url=q_url, headers=self.web_heads, verify=False)
            
            if 'questions-and-answers' in q_url:
                try:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    dd = soup.find('script', attrs={'id': '__NEXT_DATA__'})
                    js = json.loads(dd.text)
                    q_id = js['props']['pageProps']['questionResult']['question']['uuid']
                except:
                    q_id = res.text.split('questionUuid":"')[1].split('"}')[0]
                # print(q_id)
                datax = {
                    'id': 'getQuestionByUuid',
                    'operationName': 'getQuestionByUuid',
                    'variables': {
                        'questionUuid': q_id
                    }
                }

                with open('settings.json', 'r') as fp:
                    jsd = json.loads(fp.read())
                
                access_token = jsd['access_token']

                heads = {
                    'user-agent': 'CheggApp/3.39.0 (com.chegg.mobile.consumer; build:3.39.0.0; iOS 14.5.0) Alamofire/5.2.2',
                    'authorization': 'Basic MFQxOE5HYmFsUURGYzBnWkh6b3ZwZVJkN0E1Y3BMQ3g6dnRnamFZa3Ric2p4OUFPUg==',
                    'Content-Type': 'application/json',
                    'Connection': 'keep-alive',
                    'access_token': access_token
                }
                
                res = requests.post(url=self.getAns, json=datax, headers=heads, verify=False)
                js = res.json()
                totalAns = len(js['data']['getQuestionByUuid']['answers'])
                ans = ''
                filename = './answers/answer_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10)) + '.html'
                if len(js['data']['getQuestionByUuid']['answers']) > 0:
                    if js['data']['getQuestionByUuid']['answers'][0]['accessDetails']['hasAccess']:
                            for indd, i in enumerate(js['data']['getQuestionByUuid']['answers']):
                                ans += '<br><h1>Answer - ' + str(indd + 1) + '</h1><br>' + i['body']
                            with open(filename, 'w', encoding='utf-8') as fp:
                                fp.write(str(ans))
                        
                            return True, filename, 'Success'
                    else:
                        return False, '', 'You dont have access'
                else:
                    return False, '', 'Not Answered Yet!!'
            else:
                problemId = res.text.split('"problemId":"')[1].split('",')[0]
                isbn13 = res.text.split('"isbn13":"')[1].split('",')[0]
                datax = {
                    'problemId': problemId,
                    'isbn13': isbn13,
                    'userAgent': 'Mobile'
                }

                heads = {
                    'user-agent': 'CheggApp/3.39.0 (com.chegg.mobile.consumer; build:3.39.0.0; iOS 14.5.0) Alamofire/5.2.2',
                    'authorization': 'Basic MFQxOE5HYmFsUURGYzBnWkh6b3ZwZVJkN0E1Y3BMQ3g6dnRnamFZa3Ric2p4OUFPUg==',
                    'Content-Type': 'application/json',
                    'Connection': 'keep-alive'
                }

                resp1 = requests.post(url=self.tbs, json=datax, headers=heads, verify=False)
                js1 = resp1.json()
                if js1['httpCode'] == 200:
                    if len(js1['result']['solutions']) > 0:
                        filename = './answers/answer_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10)) + '.html'
                        datac = ''
                        for indd, x in enumerate(js1['result']['solutions'][0]['steps']):
                            datac += '<br><H1>Step - ' + str(indd + 1) + '<br>' + requests.get(x['link'], verify=False).text
                        
                        with open(filename, 'w', encoding='utf-8') as fp:
                            fp.write(str(datac))
                        return True, filename, 'Success'
                    
                    else:
                        return False, '', 'Not answered'
        except Exception as e:
            return False, '', str(e)
        
    def tryLogin(self, username, password):
        data = {
            'grant_type': 'password',
            'source_page': 'ios CheggApp 3.36.0|cs',
            'source_product': 'ios|cs',
            'username': username,
            'password': password
        }

        res = requests.post(url=self.log_url, data=data, headers=self.heads, verify=False)
        js = res.json()
        if res.status_code == 200:
            if 'error' in res.text:
                print('[*] ' + js['error'])
            elif js['access_token'] != None and js['mfaChallengeDetails'] == None:
                access_token = js['access_token']
                refresh_token = js['refresh_token']
                id_token = js['id_token']
                with open('settings.json', 'w') as fp:
                    data = {
                        'access_token': access_token,
                        'refresh_token': refresh_token,
                        'id_token': id_token
                    }
                    fp.write(json.dumps(data))
            elif js['mfaChallengeDetails'] != None:
                mfaToken = js['mfaChallengeDetails']['mfaToken']
                userUUID = js['mfaChallengeDetails']['userUuid']
                factors = js['mfaChallengeDetails']['factors']
                self.try2FA(mfaToken, factors)
            else:
                print('[*] Unknown Error')
        else:
            print('[*] ' + js['error'])
