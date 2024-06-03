import json
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
pixiv_notify_socket.setsockopt_string(zmq.SUBSCRIBE, '')
hitomi_req_socket = zmq_context.socket(zmq.REQ)
hitomi_notify_socket = zmq_context.socket(zmq.SUB)
hitomi_notify_socket.setsockopt_string(zmq.SUBSCRIBE, '')

jm_socket.connect('tcp://localhost:37896')
pixiv_notify_socket.connect("tcp://localhost:5556")
pixiv_req_socket.connect("tcp://localhost:5555")
hitomi_req_socket.connect('tcp://localhost:37980')
hitomi_notify_socket.connect('tcp://localhost:37890')

poller = zmq.Poller()
poller.register(pixiv_notify_socket, zmq.POLLIN)

if platform.system() == 'Windows':
    curdir = os.path.abspath('.')
else:
    curdir = '/var/www/webbot'

app.config['UPLOAD_FOLDER'] = os.path.join(curdir, 'uploads')


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
def get_jmid(jm_str=''):
    if jm_str:
        jm_id = jm_str
    else:
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


@app.route('/redirect_to_hitomi', methods=['GET'])
def redirect_to_hitomi():
    def ret_json(val):
        return 'data: ' + json.dumps(val) + '\n\n'
    jm_str = flask.request.args.get('jm_str', '')
    if not jm_str:
        return active_risk_defender('redirect_to_hitomi')
    response = {
        'type': 'json',
        'status': 'async',
        'echo': '已收到你的请求'
    }
    yield ret_json(response)
    jm_result = get_jmid(jm_str)
    if '<br>' in jm_result:
        jm_name = jm_result.split('<br>')[0]
        response['echo'] = f'已获得本名:{jm_name}'
        yield ret_json(response)
        hitomi_req_socket.send_json({'type': 'check_queue'})
        resp = hitomi_req_socket.recv_json()
        response['echo'] = f'当前hitomi队列有{resp["result"]}个请求'
        yield ret_json(response)
        hitomi_req_socket.send_json({'type': 'search', 'query_str': jm_name})
        response['echo'] = '请求已发送，耐心等待，寄了我会告诉你的'
        yield ret_json(response)
        socks = dict(poller.poll(300000))
        if hitomi_notify_socket in socks:
            req_result: list[dict] = hitomi_notify_socket.recv_json()
        else:
            response['echo'] = '不用等了，寄了'
            return ret_json(response)
        if req_result:
            gallery = req_result[0]
            response['echo'] = gallery['galleryurl']
            response['type'] = 'html'
            return ret_json(response)
    else:
        response['status'] = 'error'
        response['echo'] = 'Not Found'
        yield ret_json(response)


def search_img_upload(filename):
    api_key = 'a71bce7cb564ead10b8924be035c34950d97cde2'
    img_url = 'http://39.105.24.101/bot/upload_temp/' + filename
    if not api_key or not img_url:
        raise NotImplementedError('未配置apikey或图片地址')
    target_url = f'https://saucenao.com/search.php?db=999&api_key={api_key}&output_type=2&numres=1&url={img_url}'
    response = requests.get(target_url)
    search_result = response.json()
    retval = {
        'status': 'error',
        'result': None
    }
    if 'results' in search_result:
        retval['status'] = 'success'
        retval['result'] = search_result['results'][0]
    else:
        retval['result'] = 'API返回值没有结果'
    return retval


def active_risk_defender(echo):
    return 'nmsl' + flask.render_template('LBY_DONT_HAVE_MOM.html', image_urls=echo)


token_hash = 'fb2a9baab1c23d9786f23ff8708633a63e0e40ff98fa135585ca4491c18193be'


@app.route('/upload_imgs/<path:authToken>', methods=['POST', 'GET'])
def img_uploader(authToken):
    request = flask.request
    if authToken != token_hash:
        return active_risk_defender(authToken)
    elif authToken == 'Undefined':
        return active_risk_defender(2)
    if 'image' not in request.files or 'md5' not in request.form or 'ext' not in request.form:
        return active_risk_defender(3)
    file = request.files['image']
    md5 = request.form['md5']
    ext = request.form['ext']
    if file.filename == '':
        return active_risk_defender(4)
    if ext not in ['jpg', 'jpeg', 'png', 'webp', 'bmp']:
        return active_risk_defender(5)
    if not bool(re.compile(r'^[a-fA-F0-9]{32}$').match(md5)):
        return active_risk_defender(6)
    filename = f"{md5}.{ext}"  # 将MD5值和扩展名结合作为文件名
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename


@app.route(f'/upload_imgs/{token_hash}/<filename>')
def img_upload_sse_handler(filename):
    return flask.Response(img_upload_sse_generator(filename), mimetype='text/event-stream')


@flask.copy_current_request_context
def img_upload_sse_generator(filename):
    def ret_json(val):
        return 'data: ' + json.dumps(val) + '\n\n'

    with app.app_context(), app.test_request_context():
        response = {
            'type': 'json',
            'status': 'async',
            'echo': '开始请求SauceAPI'
        }
        yield ret_json(response)
        search_result = search_img_upload(filename)
        img_id = extract_useful_id(search_result['result'])
        if img_id > 0:
            response['echo'] = 'SauceAPI已正常返回，正在下载图片'
            yield ret_json(response)
            result = proc_pixiv_fun('dl', pid=img_id)
            if result['status'] == 'success':
                work_list = result['result']
                img_urls = [flask.url_for('static', filename=f'fpid_temp/{work}') for work in work_list]
                response['type'] = 'html'
                response['status'] = 'success'
                response['echo'] = flask.render_template('show_img.html', image_urls=img_urls)
                yield ret_json(response)
            else:
                response['status'] = 'error'
                response['echo'] = f'你的图片没法下载(不一定，可能是太大了)，这是pid:{img_id}'
                yield ret_json(response)
        else:
            response['status'] = 'error'
            if img_id == 0:
                response['echo'] = '未知的索引类型，请联系管理员'
                yield ret_json(response)
            elif img_id == -1:
                response['echo'] = '相似度过低，不予显示'
                yield ret_json(response)
            response['echo'] = '未知错误'
            yield ret_json(response)


def extract_useful_id(result_dict) -> int:
    index_id = result_dict['header']['index_id']
    similarity = result_dict['header']['similarity']
    if float(similarity) < 0.6:
        return -1
    if index_id == 5:
        return result_dict['data']['pixiv_id']
    else:
        return 0


@app.route('/get_pixiv_img_from_id', methods=['POST'])
def get_pixiv_img_from_id():
    pid = flask.request.form['pid']
    numbers = re.findall(r'\d+', pid)
    # 合并提取出的数字为一个纯数字字符串
    fmt_pid = ''.join(numbers)
    if not fmt_pid:
        return '不合法：其中无数字'
    result = proc_pixiv_fun('dl', pid=fmt_pid)
    if result['status'] == 'success':
        # 正常处理逻辑
        work_list = result['result']
        img_urls = [flask.url_for('static', filename=f'fpid_temp/{work}') for work in work_list]
        return flask.render_template('show_img.html', image_urls=img_urls)
    else:
        if result['result'][0] == 'Timeout':
            return 'Pixiv后端请求超时，多半是你请求下载的图片太大了，过会再试'
        if result['type'] == 'dl':
            if result['result'][0] == 'ページが見つかりませんでした':
                return '你请求的作品不存在'
            if result['result'][0] == 'Exceed Limit':
                return '超过十张，不予下载'
        return str(result)


@app.route('/test_img')
def test_img():
    img_urls = [
        flask.url_for('static', filename='yuuka.png')
    ]
    return flask.render_template('show_img.html', image_urls=img_urls)


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


@app.route('/upload_temp/<path:filename>')
def upload_temp(filename):
    return flask.send_from_directory(os.path.join(app.root_path, 'uploads'), filename)


if __name__ == '__main__':
    app.run(debug=True)
