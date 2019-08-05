# GatoIO交易工具

## 环境依赖
本项目在python3.7环境下经测试可正常使用

## 安装
```shell
pip install -r requirements.txt
```

## 用法
在配置文件`config.py`中填入自己的api key和secret，`REAL=False`时可用于测试，不会发起真实交易

```shell
# 查看帮助
python service.py --help
# 查看单个命令的帮助，例如
python service.py trading --help
# 自动化交易
python service.py trading --amount 10000 --num 100 --pair doge_cnyx --delta 0.00001
```

### 自动化交易
用于对敲刷量交易，即同时挂出买单和卖单，期望自己的买卖单可以完全匹配。但需要注意选择合适的交易对，兼顾价差和交易量，
交易量过大则对敲时越可能与其他用户的订单匹配从而对敲失败，此时就需要人工介入做一次反向交易进行修正（未来可能会添加程序自动修正的功能）。
当人工介入时如果价差过大，则损失可能越大。

```shell
Options:
  --amount INTEGER  单笔交易中的数量  [required]
  --num INTEGER     交易组数(一买一卖为一组)  [required]
  --pair TEXT       交易对  [required]
  --delta FLOAT     价差  [required]
  --help            Show this message and exit.
```

**注意**: 目前GatoIO上usdt_cnyx交易对是不计入VIP等级交易量的

## 联系
有任何问题和建议可以联系 **ericsgy@163.com**