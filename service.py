import click
import logging
import time
import atexit
import asyncio
from datetime import datetime
from pprint import pprint
from client import order_book, c2c_order_book as _c2c_order_book, \
    balances, cancel_orders, cancel_order, get_order, open_orders, cancel_all_orders, \
    async_balances, async_c2c_order_book as _async_c2c_order_book, async_open_orders, async_buy, \
    async_sell
from utils import make_async, retry


@click.group("main")
def portal():
    logging.getLogger().setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s %(message)s'))
    logging.getLogger().addHandler(console)


@portal.command()
def balance():
    """ 账户余额 """
    available, locked = balances()
    logging.info("可用:")
    pprint(available)
    logging.info("冻结:")
    pprint(locked)


@portal.command()
@make_async
async def async_balance():
    """ 账户余额(异步) """
    available, locked = await async_balances()
    logging.info("可用:")
    pprint(available)
    logging.info("冻结:")
    pprint(locked)


@portal.command()
@click.option("--pair", type=click.STRING, required=False, help="c2c交易对，例如usdt_cny")
def c2c_order_book(pair):
    """ c2c市场深度 """
    asks, bids = _c2c_order_book(pair)
    logging.info(f"卖单:")
    pprint(asks, width=120)
    logging.info(f"买单:")
    pprint(bids, width=120)


@portal.command()
@click.option("--pair", type=click.STRING, required=False, help="交易对")
@make_async
async def async_c2c_order_book(pair):
    """ c2c市场深度（异步） """
    asks, bids = await _async_c2c_order_book(pair)
    logging.info(f"卖单:")
    pprint(asks, width=120)
    logging.info(f"买单:")
    pprint(bids, width=120)


@portal.command()
@click.option("--pair", type=click.STRING, required=False, help="交易对")
def show_order_book(pair):
    """ 市场深度 """
    asks, bids = order_book(pair)
    logging.info(f"卖单:")
    pprint(asks, width=120)
    logging.info(f"买单:")
    pprint(bids, width=120)


@portal.command()
@click.option("--order_no", type=click.STRING, required=True)
@click.option("--pair", type=click.STRING, required=False, help="交易对")
def order(order_no, pair):
    """ 订单详情 """
    rst = get_order(order_no, pair)
    pprint(rst)


@portal.command()
@click.option("--pair", type=click.STRING, default="", required=False)
def order_list(pair):
    """ 当前挂单列表 """
    orders = open_orders(pair)
    pprint(orders)


@portal.command()
@click.option("--pair", type=click.STRING, default="", required=False)
@make_async
async def async_order_list(pair):
    """ 当前挂单列表（异步） """
    orders = await async_open_orders(pair)
    pprint(orders)


@portal.command()
@click.option("--number", type=click.STRING, required=True, help="订单号")
@click.option("--pair", type=click.STRING, required=True)
def cancel(number, pair):
    """ 取消订单 """
    rst = cancel_order(number, pair)
    click.echo(rst)


@portal.command()
@click.option("--order_pairs", type=click.STRING, required=True, help="形如order_num,currency_pair-...的短横线隔开的交易对")
def batch_cancel(order_pairs):
    """ 批量取消订单 """
    orders = []
    for pair in order_pairs.split("-"):
        order_num, currency_pair = pair.split(",")
        orders.append({"orderNumber": order_num, "currencyPair": currency_pair})
    rst = cancel_orders(orders)
    click.echo(rst)


@portal.command()
@click.option("--amount", type=click.INT, required=True, help="单笔交易中的数量")
@click.option("--num", type=click.INT, help="交易组数(一买一卖为一组)", required=True)
@click.option("--pair", type=click.STRING, required=True, help="交易对")
@click.option("--delta", type=click.FLOAT, required=True, help="价差")
@make_async
async def trading(amount: int, num: int, pair: str, delta: float):
    """ 自动化交易 """

    currency_pair = pair

    # 注册退出函数
    atexit.register(trading_finished, currency_pair)

    # 设置重试次数
    get_balance = retry(3)(balances)

    def __cancel_orders(*_order_list):
        _orders = []
        for _order in _order_list:
            if _order:
                cancel_order(_order, currency_pair)
                logging.info(f"撤销订单{_order}成功")

    currencyA, currencyB = currency_pair.split("_")
    currencyA = currencyA.upper()
    currencyB = currencyB.upper()

    # 根据delta计算有效小数位位数
    delta_str = "{:.20f}".format(delta)
    # 截取小数部分,去除有效数字后面的0
    decimal_part = delta_str[delta_str.index(".") + 1:delta_str.index("1") + 1]
    effective_length = len(decimal_part)

    # 确定初始金额
    available, _ = get_balance()
    init_currencyA = round(available[currencyA], 2)
    init_currencyB = round(available[currencyB], 2)

    for idx in range(num):
        logging.info(f"第{idx+1}轮...")
        sell_order_number = buy_order_number = None
        sell_order_num_back = sell_order_number
        buy_order_num_back = buy_order_number

        asks, bids = order_book(currency_pair)
        # logging.info(f"卖单: {asks[-3:]}")
        # logging.info(f"买单: {bids[:3]}")
        min_ask_rate, ask_amount = asks[-1]
        max_bid_rate, bid_amount = bids[0]

        min_ask_rate = float(min_ask_rate)
        max_bid_rate = float(max_bid_rate)
        # 选择挂单价格
        if min_ask_rate - delta <= max_bid_rate:
            logging.info(f"价差极小,注意风险, 最小卖单价:{min_ask_rate}, 最大买单价:{max_bid_rate}")
            time.sleep(2)
            continue
        rate = round(min_ask_rate - delta, effective_length)
        logging.info(f"本轮定价: {rate}, 交易金额: {round(rate * amount, 2)} $")

        try:
            sell_task = async_sell(currency_pair, rate, amount)
            buy_task = async_buy(currency_pair, rate, amount)
            for rst in await asyncio.gather(sell_task, buy_task):
                if rst['_type'] == "buy":
                    buy_order_number = buy_order_num_back = rst['orderNumber']
                    logging.info(f"挂单（买）成功！订单号：{buy_order_number}，时间戳：{datetime.fromtimestamp(rst['ctime'])}")
                else:
                    sell_order_number = sell_order_num_back = rst['orderNumber']
                    logging.info(f"挂单（卖）成功！订单号：{sell_order_number}，时间戳：{datetime.fromtimestamp(rst['ctime'])}")
        except Exception as e:
            logging.warning("下单异常")
            try:
                __cancel_orders(sell_order_number, buy_order_number)
                sell_order_number = buy_order_number = None
                logging.info("下单异常处理完毕")
            except:
                logging.error("批量撤销订单失败")
        time.sleep(0.5)
        available, _ = balances()
        current_currencyA = round(available[currencyA], 2)
        current_currencyB = round(available[currencyB], 2)
        if current_currencyA != init_currencyA or current_currencyB != init_currencyB:
            logging.error(f"账户余额出现异常,请立刻检查!\n"
                          f"初始余额: {currencyA}({init_currencyA}), {currencyB}({init_currencyB})\n"
                          f"当前余额: {currencyA}({current_currencyA}), {currencyB}({current_currencyB})")
            try:
                __cancel_orders(sell_order_number, buy_order_number)
            except:
                # 批量撤销失败，尝试单独撤销
                logging.warning("批量撤销订单失败")
            finally:
                logging.info(f"当前余额 -> {currencyA}: {current_currencyA}, {currencyB}: {current_currencyB}, POINT: {available['POINT']}")
                logging.info(f"卖单号: {sell_order_num_back}, 买单号: {buy_order_num_back}")
                if sell_order_num_back:
                    sell_order_info = get_order(sell_order_num_back, currency_pair)
                    logging.info("卖单信息:")
                    pprint(sell_order_info)
                if buy_order_num_back:
                    buy_order_info = get_order(buy_order_num_back, currency_pair)
                    logging.info("买单信息:")
                    pprint(buy_order_info)
            break

        logging.info(f"当前余额 -> {currencyA}: {current_currencyA}, {currencyB}: {current_currencyB}, POINT: {available['POINT']}")
        # time.sleep(1)


def trading_finished(currency_pair):
    logging.info(f"撤销所有 {currency_pair} 交易对订单")
    cancel_all_orders(-1, currency_pair)
    available, locked = balances()
    logging.info("当前账户可用余额")
    pprint(available)
    logging.info("当前账户冻结余额")
    pprint(locked)


if __name__ == '__main__':
    portal()
