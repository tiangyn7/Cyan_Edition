import asyncio
import aiohttp
import time
import json

API_URL = "http://127.0.0.1:5000/api/chat"
TEST_PROMPT = "请用一句话介绍Vue3"
MODEL_ID = "ep-20260326054350-rkpkx"  # 替换为你的实际模型ID

async def test_single(session, request_id):
    payload = {
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "model_id": MODEL_ID,
        "temperature": 0.7
    }
    start_time = time.time()
    first_token_delay = None
    status = "fail"
    try:
        async with session.post(API_URL, json=payload) as resp:
            status = resp.status
            async for line in resp.content:
                if line.startswith(b'data:') and first_token_delay is None:
                    first_token_delay = time.time() - start_time
                    break  # 仅测首Token延迟，收到后即断开
        return {"id": request_id, "status": status, "delay": first_token_delay, "error": None}
    except Exception as e:
        return {"id": request_id, "status": 0, "delay": None, "error": str(e)}

async def run_test(concurrent):
    print(f"\n===== 测试并发数: {concurrent} =====")
    async with aiohttp.ClientSession() as session:
        tasks = [test_single(session, i+1) for i in range(concurrent)]
        results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r["status"] == 200)
    delays = [r["delay"] for r in results if r["delay"] is not None]
    avg_delay = sum(delays) / len(delays) * 1000 if delays else 0
    
    print(f"成功连接数: {success_count}/{concurrent}")
    print(f"成功率: {success_count/concurrent*100:.1f}%")
    print(f"首Token平均延迟: {avg_delay:.0f}ms")
    for r in results:
        if r["error"]:
            print(f"  请求{r['id']}异常: {r['error'][:50]}")
    return success_count, avg_delay

async def main():
    for n in [5, 10, 15]:
        await run_test(n)
        await asyncio.sleep(2)  # 等待服务恢复

if __name__ == "__main__":
    asyncio.run(main())