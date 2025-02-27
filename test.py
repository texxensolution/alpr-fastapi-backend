import asyncio
import time
import httpx

async def fetch_post(id):
    async with httpx.AsyncClient() as client:
        response = await client.get(f'https://jsonplaceholder.typicode.com/posts/{id}')
        return response.json()

async def main():
    start = time.time()
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_post(i)) for i in range(1, 11)]
    responses = [task.result() for task in tasks]
    print('response', responses)
    print('Time taken:', time.time() - start)
    return responses
        
async def res():
    start = time.time()
    for i in range(1, 10):
        response = await fetch_post(i)
        print(response)
    time_taken = time.time() - start
    print('Time taken:', time_taken)

asyncio.run(res())