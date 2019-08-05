import hmac
import hashlib
import requests
import logging
import aiohttp
import asyncio
from functools import wraps


ErrorCode = {
    1: "无效请求",
    2: "无效版本",
    3: "无效请求",
    4: "没有访问权限",
    5: "Key或签名无效，请重新创建",
    6: "Key或签名无效，请重新创建",
    7: "币种对不支持",
    8: "币种不支持",
    9: "币种不支持",
    10: "验证错误",
    11: "地址获取失败",
    12: "参数为空",
    13: "系统错误，联系管理员",
    14: "无效用户",
    15: "撤单太频繁，一分钟后再试",
    16: "无效单号，或挂单已撤销",
    17: "无效单号",
    18: "无效挂单量",
    19: "交易已暂停",
    20: "挂单量太小",
    21: "资金不足",
    40: "请求太频繁，稍后再试"
}


def sign(params: dict, secret):
    byte_secret = bytes(secret, encoding='utf-8')
    sign = ''
    for k, v in params.items():
        sign += k + '=' + str(v) + '&'
    bsign = bytes(sign[:-1], encoding='utf-8')
    rst = hmac.new(byte_secret, bsign, hashlib.sha512).hexdigest()
    return rst


def post(url, resource, params, api_key, secret):
    r = requests.post(
        url + resource,
        data=params,
        headers={
            "KEY": api_key,
            "SIGN": sign(params, secret)
        },
        timeout=5
    )
    rst = r.json()
    if rst['result'] == "true" or rst['result'] is True:
        return rst
    # 处理错误
    code = rst['code']
    logging.error(f"API调用失败: {ErrorCode.get(code, rst['message'])}")
    raise Exception(ErrorCode.get(code, rst['message']))


def get(url, resource, params=None):
    r = requests.get(url + resource, params, timeout=5)
    rst = r.json()
    if rst['result'] == "true":
        return rst
    # 处理错误
    code = rst['code']
    logging.error(f"API调用失败: {ErrorCode[code]}")
    raise Exception(ErrorCode[code])


timeout = aiohttp.ClientTimeout(total=5)


async def async_get(url, resource, params=None):
    async with aiohttp.ClientSession(timeout=timeout) as session:
        response = await session.get(url + resource, params=params, timeout=timeout)
        rst = await response.json()
        return rst


async def async_post(url, resource, params, api_key, secret):
    async with aiohttp.ClientSession(timeout=timeout) as session:
        response = await session.post(url + resource, data=params, headers={
            "KEY": api_key,
            "SIGN": sign(params, secret)
        })
        rst = await response.json()
        if rst['result'] == "true" or rst['result'] is True:
            return rst
        # 处理错误
        code = rst['code']
        logging.error(f"API调用失败: {ErrorCode.get(code, rst['message'])}")
        raise Exception(ErrorCode.get(code, rst['message']))


def make_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(func(*args, **kwargs))
        loop.close()
    return wrapper


def retry(n):
    def _wrapper1(func):
        @wraps(func)
        def _wrapper2(*args, **kwargs):
            e = None
            for _ in range(n):
                try:
                    return func(*args, **kwargs)
                except Exception as _e:
                    e = _e
            else:
                raise Exception(e)
        return _wrapper2
    return _wrapper1


