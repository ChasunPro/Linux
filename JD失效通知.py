#[public:true]
#[author: hdbjlizhe]
#[version: 1.0.0]
#[class: 工具类]
#[title: JD失效通知]
#[class: 工具类]
#[price: 0.01]
#[priority: 999]
#[class: 工具类]
#[description: 检测账号有效性]
#[disable:false]
#[rule: ^检测失效$]
#[cron:55 * * * *]
#[admin: true] 是否为管理员指令
#[param: {"required":true,"key":"otto.jd_ql","bool":false,"placeholder":"JD容器","name":"jd_ql","desc":"JD容器"}]
#[param: {"required":true,"key":"otto.tz_type","bool":false,"placeholder":"通知平台","name":"tz_type","desc":"例如：qq,wx"}]


import middleware,json,requests
from urllib.parse import unquote_plus

# 获取青龙token
class qinglong:
    def __init__(self,ql_ipport, client_id, client_secret):
        self.ql_ipport = ql_ipport
        self.client_id = client_id
        self.client_secret = client_secret
        self.ql_token = ''
    
    # 获取token
    def get_ql_token(self):
        url = f'{self.ql_ipport}/open/auth/token?client_id={self.client_id}&client_secret={self.client_secret}'
        res = requests.get(url).json()
        # print(res)
        if res.get('code') == 200:
            self.ql_token = res.get('data').get('token')
        else:
            print('连接青龙失败')
        
    # 查询环境变量
    def get_ql_env(self,value):
        url = f'{self.ql_ipport}/open/envs?searchValue={value}'
        headers = {'Authorization': f'Bearer {self.ql_token}'}
        res = requests.get(url,headers=headers).json()
        # print(res)
        if res.get('code') == 200:
            return res.get('data')
    
    # 新增环境变量
    def submit_env(self,json):
        url = f'{self.ql_ipport}/open/envs'
        headers = {'Authorization': f'Bearer {self.ql_token}'}
        # json = [{"value":value,"name":name,"remarks":remarks}]
        res = requests.post(url,headers=headers,json=json).json()
        # print(res)
        if res.get('code') == 200:
            return True
        else:
            print(res.get('message'))
    
    # 更新环境变量
    def update_env(self,name,value,remarks,id):
        url = f'{self.ql_ipport}/open/envs'
        headers = {'Authorization': f'Bearer {self.ql_token}'}
        json = {"name":name,"value":value,"remarks":remarks,"id":id}
        res = requests.put(url,headers=headers,json=json).json()
        # print(res)
        if res.get('code') == 200:
            return True
    
    # 删除环境变量
    def delete_env(self,json):
        url = f'{self.ql_ipport}/open/envs'
        headers = {'Authorization': f'Bearer {self.ql_token}'}
        # json = [id]
        res = requests.delete(url,headers=headers,json=json).json()
        # print(res)
        if res.get('code') == 200:
            return True
    
    # 禁用环境变量
    def disable_env(self,id):
        url = f'{self.ql_ipport}/open/envs/disable'
        headers = {'Authorization': f'Bearer {self.ql_token}'}
        json = [id]
        res = requests.put(url,headers=headers,json=json).json()
        # print(res)
        if res.get('code') == 200:
            return True
    
    # 启用环境变量
    def enable_env(self,id):
        url = f'{self.ql_ipport}/open/envs/enable'
        headers = {'Authorization': f'Bearer {self.ql_token}'}
        json = [id]
        res = requests.put(url,headers=headers,json=json).json()
        # print(res)
        if res.get('code') == 200:
            return True


def check(ck):
    url = 'https://plogin.m.jd.com/cgi-bin/ml/islogin'
    headers = {
        "Cookie": ck,
        "referer": "https://h5.m.jd.com/",
        "User-Agent": "jdapp;iPhone;10.1.2;15.0;network/wifi;Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148;supportJDSHWK/1",
    }
    res = requests.get(url, headers=headers).json()
    islogin = res['islogin']
    if islogin == '1':
        return True
    else:
        return False

def get_ql(sender,need_name):
    qls = sender.bucketAllKeys('qls')
    for i in qls:
        ql = json.loads(sender.bucketGet('qls', i))
        host = ql.get('host')
        client_id = ql.get('client_id')
        client_secret = ql.get('client_secret')
        name = ql.get('name')
        if need_name == name:
            print('成功找到容器')
            return host,client_id,client_secret
    
def main(sender):
    middleware.notifyMasters(f'开始检测{ql_name}.....')
    isLive_list = []
    unLive_list = []
    # 获取容器
    host,client_id,client_secret = get_ql(sender,ql_name)
    default_ql = qinglong(host,client_id,client_secret)
    default_ql.get_ql_token()

    # 获取默认容器jdck
    cks = default_ql.get_ql_env(yangmao_env)
    for ck in cks:
        ck = ck.get('value')
        pt_pin = ck.split('pt_pin=')[1].split(';')[0]
        # 检测ck是否有效
        isLive = check(ck)
        if isLive: #有效
            isLive_list.append(pt_pin)
            continue
        else: # 无效
            unLive_list.append(pt_pin)
    
    qls = sender.bucketAllKeys('qls')
    # 去禁用所有容器对应的ck
    for i in qls:
        ql = json.loads(sender.bucketGet('qls', i))
        host = ql.get('host')
        client_id = ql.get('client_id')
        client_secret = ql.get('client_secret')
        name = ql.get('name')
        ql = qinglong(host,client_id,client_secret)
        ql.get_ql_token()
        for pt_pin in unLive_list:
            values = ql.get_ql_env(pt_pin)
            if values:
                for value in values:
                    ql.disable_env(value['id'])

    middleware.notifyMasters(f'✅检测完成\n总帐号：{len(cks)}\n有效账号：{len(isLive_list)}\n失效账号：{len(unLive_list)}')

    for imType in imTypes:
        groupCode = ''
        title = '📢京东账号失效通知'
        # 去通知
        for pin in unLive_list:
            pin = unquote_plus(pin)
            userID = middleware.bucketGet(f'pin{imType.upper()}',pin)
            content = f'\n您的账号{pin}已失效，请重新登陆'
            if '@' in userID:
                content += f'\n请您添加机器人好友后再登陆，避免查询不到！'
            middleware.push(imType,groupCode,userID,title,content)
    
    middleware.notifyMasters(f'✅通知完成')

if __name__ == '__main__':
    senderID = middleware.getSenderID()
    sender = middleware.Sender(senderID)
    
    yangmao_env = 'JD_COOKIE'
    ql_name = middleware.bucketGet('otto','jd_ql')
    imTypes = middleware.bucketGet('otto','tz_type').split(',')
    main(sender)