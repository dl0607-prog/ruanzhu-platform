# 演示库存管理系统 V1.0

这是能运行的教学案例，演示申请信息、源码、说明书、申请表、检查和导出。不是已经获证的软件，也不能直接作为用户实际项目申报。程序由AI辅助生成，应如实核实人工贡献和权属。

## 运行

需要Python 3.9或以上，无需第三方库。在此目录运行：

```sh
python3 inventory.py add P001 无线鼠标
python3 inventory.py in P001 20
python3 inventory.py out P001 3
python3 inventory.py list
python3 inventory.py history
```

库存应为17；出库99会被拒绝。数据保存在inventory.sqlite3。实际运行记录使用临时数据库验证，包括超额出库后库存仍为17。

## 在平台里体验

新建“演示库存管理系统”项目，上传inventory.py；在“准备材料”录入随附说明书和真实申请表参考字段，然后“检查问题”并“下载材料”。没有配置AI也可以完成该流程。演示申请人不是实际身份；三项人工核对不能为展示而虚假勾选。
