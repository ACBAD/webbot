import asyncio
import aioconsole
import zmq
from aioconsole import aprint
from BetterPixiv_Async import BetterPixiv


async def create_action(api: BetterPixiv, command: str, *args) -> dict:
    respone = {'status': 'success', 'result': []}
    sudo = False
    if command == 'dl_sudo':
        command = 'dl'
        sudo = True
    if command == 'dl':
        if len(args) < 1:
            respone['status'] = 'failed'
            respone['result'] = ['Missing Params']
            return respone
        work_id = args[0]
        dl_status = await api.download(work_id, sudo=sudo)
        respone['result'] = dl_status['paths']
        if dl_status['total'] == 0 or dl_status['total'] - dl_status['success'] != 0:
            respone['status'] = 'failed'
            respone['result'] = [dl_status['extraInfo']]
    elif command == 'user_info':
        # 13371450
        if len(args) < 1:
            respone['status'] = 'failed'
            respone['result'] = ['Missing Params']
            return respone
        user_id = args[0]
        user_info = await api.get_user_works(user_id)
        respone['result'] = user_info
    elif command == 'favs':
        fav_list = await api.get_favs()
        respone['result'] = fav_list
    elif command == 'follow':
        work_list = await api.get_new_works()
        respone['result'] = work_list
    elif command == 'chk_local':
        noloacl = await api.get_nolocal_works()
        respone['result'] = noloacl
    elif command == 'dl_nolocal':
        noloacl = await api.get_nolocal_works()
        failed_works = await api.multi_download(noloacl)
        respone['result'] = failed_works
        if failed_works:
            respone['status'] = 'failed'
    else:
        respone['status'] = 'failed'
        respone['result'] = ['Invalid Method']
    return respone

async def shell_command(queue: asyncio.Queue):
    while True:
        command = await aioconsole.ainput('Input Command:')
        if command == 'exit':
            await queue.put({'type': 'shutdown'})
            break
        com_args = command.split(' ')
        command = com_args[0]
        del com_args[0]
        if com_args:
            await queue.put({'type': command, 'args': com_args[0]})
        else:
            await queue.put({'type': command, 'args': com_args})

async def zmq_server(socket: zmq.Context.socket, queue: asyncio.Queue):
    try:
        while True:
            # 接收请求
            message = await asyncio.to_thread(socket.recv_json)
            if 'type' not in message or 'args' not in message:
                print(f'ERROR:收到的消息{message}不合法')
                continue
            print("收到请求:", message['type'])
            # 发送响应
            response = {
                'type': message['type'],
                'status': 'async'
            }
            if message['type'] == 'shutdown':
                response['status'] = 'failed'
                response['reason'] = 'No authority'
                socket.send_json(response)
                continue
            elif message['type'] == 'chk_queue':
                response = {
                    'type': message['type'],
                    'status': 'success',
                    'result': queue.qsize()
                }
                socket.send_json(response)
                continue
            socket.send_json(response)
            await queue.put(message)
    except zmq.ZMQError:
        print('服务端下线')

async def run_func(socket: zmq.Context.socket, queue: asyncio.Queue):
    api = BetterPixiv(proxy='http://127.0.0.1:10809')
    await api.api_login(refresh_token='a4TF-gC5kRkciAiZ5MhGUoVw6zb3AXO1M1DmnAeFGlk')
    api.set_storge_path('../static/fpid_temp')
    while True:
        reply = await queue.get()
        if reply['type'] == 'shutdown':
            break
        req_result = await create_action(api, reply['type'], reply['args'])
        response = {
            'type': reply['type'],
            'status': req_result['status'],
            'result': req_result['result']
        }
        socket.send_json(response)
        if req_result['status'] == 'failed':
            await aprint(f'执行{reply["type"]}时出错:{req_result["result"][0]}')
        else:
            await aprint(f'执行结果{req_result["result"]}')
    await api.shutdown()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    context = zmq.Context()
    listen_socket = context.socket(zmq.REP)
    notify_socket = context.socket(zmq.PUB)
    listen_socket.bind("tcp://*:5555")  # 绑定端口
    notify_socket.bind('tcp://*:5556')
    zmq_queue = asyncio.Queue()
    loop.create_task(shell_command(zmq_queue))
    loop.create_task(zmq_server(listen_socket, zmq_queue))
    loop.run_until_complete(run_func(notify_socket, zmq_queue))
    listen_socket.close()
    notify_socket.close()
    context.term()
