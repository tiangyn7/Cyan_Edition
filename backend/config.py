import os
from dotenv import load_dotenv
from volcenginesdkarkruntime import Ark

# 获取当前目录下的 Key.env
current_dir = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(current_dir, 'Key.env')
load_dotenv(dotenv_path=key_path)

# 从环境变量读取 Key
api_key = os.getenv("YOUR_API_KEY")

if not api_key:
    raise ValueError(f"未找到 API Key，请检查文件：{key_path}")

# 初始化 Ark 客户端 (必须指定 v3 路径)
client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=api_key
)
print("后端 Ark V3 客户端初始化成功")