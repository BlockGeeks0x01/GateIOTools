from functools import partial
from pprint import pprint

from config import APIKEY, SECRET, DATA_URL, PRIVATE_URL, REAL
from utils import post, get, async_get, async_post

post = partial(post, api_key=APIKEY, secret=SECRET)
async_post = partial(async_post, api_key=APIKEY, secret=SECRET)


def funding_balances():
    """ 理财账号资金余额 """
    rst = post(PRIVATE_URL, "/fundingbalances", {})
    return rst


def balances():
    """
    账号资金余额
    :return:
        {
            "result": "true",
            "available": {
                "BTC": "1000",
                "ETH": "968.8",
                "ETC": "0",
                },
            "locked": {
                "ETH": "1"
                }
        }
    """
    min_value = 0.001
    rst = post(PRIVATE_URL, "/balances", {})
    available, locked = rst['available'], rst['locked']

    for d in (available, locked):
        for k in d.keys():
            d[k] = round(float(d[k]), 6)
    available = {k: v for k, v in available.items() if v > min_value}
    locked = {k: v for k, v in locked.items() if v > min_value}
    return available, locked


async def async_balances():
    min_value = 0.001
    rst = await async_post(PRIVATE_URL, "/balances", {})
    available, locked = rst['available'], rst['locked']

    for d in (available, locked):
        for k in d.keys():
            d[k] = round(float(d[k]), 6)
    available = {k: v for k, v in available.items() if v > min_value}
    locked = {k: v for k, v in locked.items() if v > min_value}
    return available, locked


def trade_pairs():
    """ 所有交易对 """
    rst = get(DATA_URL, "/pairs")
    return rst


def order_book(currency_pair: str):
    """
    市场深度(委托挂单/买单)
    :param currency_pair: 交易对
    :return:
      {
        "result": "true",
        "asks": [   // 卖方深度
                [29500,    4.07172355],
                [29499,    0.00203397],
                [29495,    1],
                [29488,    0.0672],
                [29475,    0.001]
            ],
        "bids": [   // 买方深度
                [28001, 0.0477],
                [28000, 0.35714018],
                [28000, 2.56222976],
                [27800, 0.0015],
                [27777, 0.1]
            ]
        }
    """
    rst = get(DATA_URL, "/orderBook/" + currency_pair)
    asks = rst['asks']
    bids = rst['bids']
    return asks, bids


def c2c_order_book(currency_pair: str):
    """
    返回系统支持的所有C2C交易对的市场深度（委托挂单）
    :param currency_pair:
    :return:
        [价格，数量，单笔最小交易量，单笔最大交易量]
    """
    rst = get(DATA_URL, "/orderBook_c2c/" + currency_pair)
    asks, bids = rst['asks'], rst['bids']
    asks = [{"price": item[0], "amount": item[1], "min_amount": item[2], "max_amount": item[3]} for item in asks]
    bids = [{"price": item[0], "amount": item[1], "min_amount": item[2], "max_amount": item[3]} for item in bids]
    return asks, bids


async def async_c2c_order_book(currency_pair: str):
    rst = await async_get(DATA_URL, "/orderBook_c2c/" + currency_pair)
    asks, bids = rst['asks'], rst['bids']
    asks = [{"price": item[0], "amount": item[1], "min_amount": item[2], "max_amount": item[3]} for item in asks]
    bids = [{"price": item[0], "amount": item[1], "min_amount": item[2], "max_amount": item[3]} for item in bids]
    return asks, bids


def open_orders(currency_pair=""):
    """ 当前挂单列表 """
    rst = post(PRIVATE_URL, "/openOrders", {"currencyPair": currency_pair})
    return rst['orders']


async def async_open_orders(currency_pair=""):
    rst = await async_post(PRIVATE_URL, "/openOrders", {"currencyPair": currency_pair})
    return rst['orders']


def trade_history(currency_pair=""):
    """ 24小时内成交记录 """
    rst = post(PRIVATE_URL, "/tradeHistory", {"currencyPair": currency_pair})
    return rst['trades']


def buy(currency_pair: str, rate: float, amount: int, order_type=""):
    """
    下单交易买入
    :param currency_pair: 交易对 ltc_btc
    :param rate: 价格
    :param amount: 交易量
    :param order_type: 订单类型,默认是普通; ioc,立即执行否则取消订单
    :return:
        {
            "result":"true",
            "orderNumber":"123456", // 订单号，可用于查询/取消订单
            "rate":"1000",  // 下单价格
            "leftAmount":"0",   // 剩余数量
            "filledAmount":"0.1",   // 成交数量
            "filledRate":"800.00",  // 成交价格
            "message":"Success"
        }
    """
    params = {
        "currencyPair": currency_pair,
        "rate": str(rate),
        "amount": str(amount),
        "orderType": order_type
    }

    if REAL:
        rst = post(PRIVATE_URL, "/buy", params)
        return rst
    else:
        pprint(params)
        return {"result": "true", "orderNumber": None}


async def async_buy(currency_pair: str, rate: float, amount: int, order_type=""):
    params = {
        "currencyPair": currency_pair,
        "rate": str(rate),
        "amount": str(amount),
        "orderType": order_type
    }
    if REAL:
        rst = await async_post(PRIVATE_URL, "/buy", params)
        rst['_type'] = "buy"
        return rst
    else:
        pprint(params)
        return {"result": "true", "orderNumber": None}


def sell(currency_pair: str, rate: float, amount: int, order_type=""):
    """
    下单交易卖出
    :param currency_pair: 交易对 ltc_btc
    :param rate: 价格
    :param amount: 交易量
    :param order_type: 订单类型,默认是普通; ioc,立即执行否则取消订单
    :return:
        {
            "result":"true",
            "orderNumber":"123456", // 订单号，可用于查询/取消订单
            "rate":"1000",  // 下单价格
            "leftAmount":"0",   // 剩余数量
            "filledAmount":"0.1",   // 成交数量
            "filledRate":"800.00",  // 成交价格
            "message":"Success"
        }
    """
    params = {
        "currencyPair": currency_pair,
        "rate": str(rate),
        "amount": str(amount),
        "orderType": order_type
    }

    if REAL:
        rst = post(PRIVATE_URL, "/sell", params)
        return rst
    else:
        pprint(params)
        return {"result": "true", "orderNumber": None}


async def async_sell(currency_pair: str, rate: float, amount: int, order_type=""):
    params = {
        "currencyPair": currency_pair,
        "rate": str(rate),
        "amount": str(amount),
        "orderType": order_type
    }

    if REAL:
        rst = await async_post(PRIVATE_URL, "/sell", params)
        rst['_type'] = "sell"
        return rst
    else:
        pprint(params)
        return {"result": "true", "orderNumber": None}


def cancel_order(order_number: str, currency_pair: str):
    """
    取消订单
    :param order_number:
    :param currency_pair:
    :return: {"result":"true","message":"Success"}
    """
    params = {"orderNumber": order_number, "currencyPair": currency_pair}
    rst = post(PRIVATE_URL, "/cancelOrder", params)
    return rst


def cancel_orders(order_pairs: [dict]):
    """
    批量取消订单(此方法目前有问题，无法使用)
    :param order_pairs:
    [{
        "orderNumber":"7942422",
        "currencyPair":"ltc_btc"
     },{
        "orderNumber":"7942423",
        "currencyPair":"ltc_btc"
        }
    ]
    :return:
    """
    rst = post(PRIVATE_URL, "/cancelOrders", {"orders_json": order_pairs})
    return rst


def cancel_all_orders(_type: int, currency_pair: str):
    """
    取消所有订单
    :param _type: 下单类型(0:卖出,1:买入,-1:不限制)
    :param currency_pair:
    :return:
    """
    params = {
        "type": _type,
        "currencyPair": currency_pair
    }
    rst = post(PRIVATE_URL, "/cancelAllOrders", params)
    return rst


def get_order(order_number: str, currency_pair: str):
    """
    获取订单信息
    :param order_number:
    :param currency_pair:
    :return:
        {
            "result":"true",
            "order":{
                "id":"15088",
                "status":"cancelled",   // 订单状态 open已挂单 cancelled已取消 closed已完成
                "currencyPair":"eth_btc",
                "type":"sell",  // 买卖类型 sell卖出, buy买入
                "rate":811, // 价格
                "amount":"0.39901357", // 买卖数量
                "initialRate":811, // 下单价格
                "initialAmount":"1"     // 下单量
                },
            "message":"Success"
        }
    """
    params = {
        "orderNumber": order_number,
        "currencyPair": currency_pair
    }
    rst = post(PRIVATE_URL, "/getOrder", params)
    return rst['order']


if __name__ == '__main__':
    pprint(trade_history("vidy_usdt"))
