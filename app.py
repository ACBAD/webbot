import os
import platform
import random
import re
import flask
import requests
import zmq

app = flask.Flask(__name__)
zmq_context = zmq.Context()
jm_socket = zmq_context.socket(zmq.REQ)
pixiv_notify_socket = zmq_context.socket(zmq.SUB)
pixiv_req_socket = zmq_context.socket(zmq.REQ)
pixiv_notify_socket.setsockopt_string(zmq.SUBSCRIBE, '')  # 订阅所有消息

jm_socket.connect('tcp://localhost:37896')
pixiv_notify_socket.connect("tcp://localhost:5556")
pixiv_req_socket.connect("tcp://localhost:5555")

poller = zmq.Poller()
poller.register(pixiv_notify_socket, zmq.POLLIN)

if platform.system() == 'Windows':
    curdir = os.path.abspath('.')
else:
    curdir = '/var/www/webbot'

def extract_useful_id(result_dict):
    index_id = result_dict['header']['index_id']
    if index_id == 5:
        return result_dict['data']['pixiv_id']
    return 0

def proc_pixiv_fun(command, **kwargs) -> dict:
    message = ''
    if command == 'dl':
        req_msg = {
            'type': 'dl',
            'args': kwargs['pid']
        }
        pixiv_req_socket.send_json(req_msg)
        message = pixiv_req_socket.recv_json()
        if message["type"] == 'error' or message['type'] == 'failed':
            return message
        socks = dict(poller.poll(10000))
        message = ''
        if pixiv_notify_socket in socks:
            message = pixiv_notify_socket.recv_json()
        if not message:
            message = {
                'status': 'failed',
                'result': ['Timeout']
            }
    elif command == 'chk_queue':
        req_msg = {
            'type': 'chk_queue',
            'args': []
        }
        pixiv_req_socket.send_json(req_msg)
        message = pixiv_req_socket.recv_json()
    return message

@app.route('/')
def hello():
    img_dir = os.path.join(curdir, 'models/pixiv_download')
    img_list = os.listdir(img_dir)
    img_name = random.choice(img_list)
    img_url = flask.url_for('random_img', filename=img_name)
    return flask.render_template('index.html', random_img_url=img_url)

@app.route('/get_jmid', methods=['POST'])
def get_jmid():
    jm_id = flask.request.form['jmid']
    numbers = re.findall(r'\d+', jm_id)
    # 合并提取出的数字为一个纯数字字符串
    fmt_jmid = ''.join(numbers)
    if not fmt_jmid:
        return '不合法：其中无数字'
    req = {
        'type': 'jmid',
        'jmid': fmt_jmid
    }
    jm_socket.send_json(req)
    pure_rep = jm_socket.recv_json()
    req['type'] = 'jmid_ori'
    jm_socket.send_json(req)
    ori_rep = jm_socket.recv_json()
    if pure_rep['status'] == 'success':
        return f'{pure_rep["result"]}<br>{ori_rep["result"]}'
    else:
        return 'Not Found'

@app.route('/get_pixiv_img_from_id', methods=['POST'])
def get_pixiv_img_from_id():
    storage_path = os.path.join(curdir, 'static/fpid_temp')
    pid = flask.request.form['pid']
    numbers = re.findall(r'\d+', pid)
    # 合并提取出的数字为一个纯数字字符串
    fmt_pid = ''.join(numbers)
    if not fmt_pid:
        return '不合法：其中无数字'
    result = proc_pixiv_fun('dl', pid=fmt_pid)
    if result['status'] == 'success':
        #正常处理逻辑
        work_list = result['result']
        img_urls = [flask.url_for('static', filename=f'fpid_temp/{work}') for work in work_list]
        return flask.render_template('show_img.html', image_urls=img_urls)
    else:
        if result['result'][0] == 'Timeout':
            return 'Pixiv后端请求超时，多半是你请求下载的图片太大了，过会再试'
        if result['type'] == 'dl':
            if result['result'][0] == 'ページが見つかりませんでした':
                return '你请求的作品不存在'
        return str(result)

@app.route('/search_img', methods=['GET', 'POST'])
def search_img():
    debug = True
    if debug:
        pic_name = 'yuuka.png'
    else:
        pic_name = flask.request.form['pic_name']
    img_url = flask.url_for('search_temp', filename=pic_name)
    host_url = 'http://39.105.24.101'
    img_url = host_url + img_url
    api_key = 'a71bce7cb564ead10b8924be035c34950d97cde2'
    target_url = f'https://saucenao.com/search.php?db=999&api_key={api_key}&output_type=2&numres=16&url={img_url}'
    response = requests.get(target_url).json()
    if 'results' not in response:
        return f'你有问题，拿着下边这个去找管理员<br>{pic_name}'
    response = response['results']
    responses = response[:3]
    for result in responses:
        work_id = extract_useful_id(result)
        if work_id != 0:
            return str(work_id)
        else:
            return '找不到叻'

@app.route('/test_img')
def test_img():
    img_urls = [
        flask.url_for('static', filename='yuuka.png')
    ]
    return flask.render_template('show_img.html', image_urls=img_urls)

@app.route('/ajax_test', methods=['POST'])
def ajax_test():
    data = flask.request.get_json()
    response = {'message': f"Hello, {data['name']}!"}
    return flask.jsonify(response)

@app.route('/req_queue', methods=['POST'])
def req_queue():
    data = flask.request.get_json()
    response = {'message': 'error:请联系管理员'}
    if data['type'] == 'jm':
        response = {'message': 'jm目前不需要使用队列，所以慢慢等就行'}
    elif data['type'] == 'pixiv':
        result = proc_pixiv_fun('chk_queue')
        if result['status'] == 'success':
            response = {'message': f'目前pixiv队列里有{result["result"]}个请求'}
    return flask.jsonify(response)

@app.route('/random_img/<path:filename>')
def random_img(filename):
    return flask.send_from_directory(os.path.join(app.root_path, 'models/pixiv_download'), filename)

@app.route('/search_temp/<path:filename>')
def search_temp(filename):
    return flask.send_from_directory(os.path.join(app.root_path, 'static/search_temp'), filename)

@app.route('/test_notify')
def test_notify():
    socks = dict(poller.poll(10000))
    message = ''
    if pixiv_notify_socket in socks:
        message = pixiv_notify_socket.recv_json()
    if not message:
        return '煞笔了吧，而毙'
    else:
        return str(message)

if __name__ == '__main__':
    app.run(debug=True)
