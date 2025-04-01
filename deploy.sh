#!/bin/bash
# 更新pip
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# 启动应用
gunicorn -w 4 -b 0.0.0.0:5000 app:app 