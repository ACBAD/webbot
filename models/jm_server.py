from jm_moduel import jm_tankobon
import zmq
import asyncio
import aioconsole

zmq_context = zmq.Context()
zmq_socket = zmq_context.socket(zmq.REP)
zmq_socket.bind('tcp://127.0.0.1:37896')
jm_api = jm_tankobon()


async def zmq_server():
    try:
        while True:
            req = await asyncio.to_thread(zmq_socket.recv_json)
            if 'type' not in req:
                zmq_socket.send_json({'status': 'error'})
                continue
            response = {
                'status': 'success',
                'result': ''
            }
            if req['type'] == 'jmid':
                jmid = req['jmid']
                bon_name = jm_api.get_pure_name(jmid)
                if bon_name:
                    response['result'] = bon_name
                else:
                    response['status'] = 'failed'
            if req['type'] == 'jmid_ori':
                jmid = req['jmid']
                ori_name = jm_api.get_origin_name(jmid)
                if ori_name:
                    response['result'] = ori_name
                else:
                    response['status'] = 'failed'
            zmq_socket.send_json(response)
    except zmq.ZMQError as e:
        zmq_socket.close()
        zmq_context.term()
        print('shutdown')


async def shell():
    while True:
        usr_in = await aioconsole.ainput('Waiting Command')
        if usr_in == 'exit':
            zmq_socket.close()
            zmq_context.term()
            print('Server shutdown')
            break


loop = asyncio.get_event_loop()
loop.create_task(zmq_server())
loop.run_until_complete(shell())
print('app shutdown')
