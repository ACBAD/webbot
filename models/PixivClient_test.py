import zmq

context = zmq.Context()
notify_socket = context.socket(zmq.SUB)
req_socket = context.socket(zmq.REQ)
poller = zmq.Poller()
poller.register(notify_socket, zmq.POLLIN)
notify_socket.connect("tcp://localhost:5556")
req_socket.connect("tcp://localhost:5555")
notify_socket.setsockopt_string(zmq.SUBSCRIBE, '')  # 订阅所有消息
while True:
    command = input('键入命令')
    if command == 'exit':
        break
    command = command.split(' ')
    req_msg = {
        'type': command[0],
        'args': '112944215'
    }
    req_socket.send_json(req_msg)
    message = req_socket.recv_json()
    print(message)
    socks = dict(poller.poll(5000))
    message = ''
    if notify_socket in socks:
        if socks[notify_socket] == zmq.POLLIN:
            message = notify_socket.recv_json()
    if not message:
        message = '超时'
    print("Received message:", message)
notify_socket.close()
req_socket.close()
context.term()
