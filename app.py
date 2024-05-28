import hashlib
import os
import platform
import random
import re
from datetime import datetime

import flask
import requests
import zmq
from werkzeug.utils import secure_filename

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

app.config['UPLOAD_FOLDER'] = os.path.join(curdir, 'uploads')

temp = {'header': dict(user_id='122462', account_type='1', short_limit='4', long_limit='100', long_remaining=99,
                       short_remaining=3, status=0, results_requested=5,
                       index={'0': {'status': 0, 'parent_id': 0, 'id': 0, 'results': 5},
                              '2': {'status': 0, 'parent_id': 2, 'id': 2, 'results': 5},
                              '5': {'status': 0, 'parent_id': 5, 'id': 5, 'results': 5},
                              '51': {'status': 0, 'parent_id': 5, 'id': 51, 'results': 5},
                              '52': {'status': 0, 'parent_id': 5, 'id': 52, 'results': 5},
                              '53': {'status': 0, 'parent_id': 5, 'id': 53, 'results': 5},
                              '6': {'status': 0, 'parent_id': 6, 'id': 6, 'results': 5},
                              '8': {'status': 0, 'parent_id': 8, 'id': 8, 'results': 5},
                              '9': {'status': 0, 'parent_id': 9, 'id': 9, 'results': 10},
                              '10': {'status': 0, 'parent_id': 10, 'id': 10, 'results': 5},
                              '11': {'status': 0, 'parent_id': 11, 'id': 11, 'results': 5},
                              '12': {'status': 0, 'parent_id': 9, 'id': 12, 'results': 10},
                              '16': {'status': 0, 'parent_id': 16, 'id': 16, 'results': 5},
                              '18': {'status': 0, 'parent_id': 18, 'id': 18, 'results': 5},
                              '19': {'status': 0, 'parent_id': 19, 'id': 19, 'results': 5},
                              '20': {'status': 0, 'parent_id': 20, 'id': 20, 'results': 5},
                              '21': {'status': 0, 'parent_id': 21, 'id': 21, 'results': 5},
                              '211': {'status': 0, 'parent_id': 21, 'id': 211, 'results': 5},
                              '22': {'status': 0, 'parent_id': 22, 'id': 22, 'results': 5},
                              '23': {'status': 0, 'parent_id': 23, 'id': 23, 'results': 5},
                              '24': {'status': 0, 'parent_id': 24, 'id': 24, 'results': 5},
                              '25': {'status': 0, 'parent_id': 9, 'id': 25, 'results': 10},
                              '26': {'status': 0, 'parent_id': 9, 'id': 26, 'results': 10},
                              '27': {'status': 0, 'parent_id': 9, 'id': 27, 'results': 10},
                              '28': {'status': 0, 'parent_id': 9, 'id': 28, 'results': 10},
                              '29': {'status': 0, 'parent_id': 9, 'id': 29, 'results': 10},
                              '30': {'status': 0, 'parent_id': 9, 'id': 30, 'results': 10},
                              '31': {'status': 0, 'parent_id': 31, 'id': 31, 'results': 5},
                              '32': {'status': 0, 'parent_id': 32, 'id': 32, 'results': 5},
                              '33': {'status': 0, 'parent_id': 33, 'id': 33, 'results': 5},
                              '34': {'status': 0, 'parent_id': 34, 'id': 34, 'results': 5},
                              '341': {'status': 0, 'parent_id': 341, 'id': 341, 'results': 5},
                              '35': {'status': 0, 'parent_id': 35, 'id': 35, 'results': 5},
                              '36': {'status': 0, 'parent_id': 36, 'id': 36, 'results': 5},
                              '37': {'status': 0, 'parent_id': 37, 'id': 37, 'results': 5},
                              '371': {'status': 0, 'parent_id': 371, 'id': 371, 'results': 5},
                              '38': {'status': 0, 'parent_id': 38, 'id': 38, 'results': 5},
                              '39': {'status': 0, 'parent_id': 39, 'id': 39, 'results': 5},
                              '40': {'status': 0, 'parent_id': 40, 'id': 40, 'results': 5},
                              '41': {'status': 0, 'parent_id': 41, 'id': 41, 'results': 5},
                              '42': {'status': 0, 'parent_id': 42, 'id': 42, 'results': 5},
                              '43': {'status': 0, 'parent_id': 43, 'id': 43, 'results': 5},
                              '44': {'status': 0, 'parent_id': 44, 'id': 44, 'results': 5}}, search_depth='128',
                       minimum_similarity=48.43, query_image_display='/userdata/SCt4tRGx8.jpg.png',
                       query_image='SCt4tRGx8.jpg', results_returned=5), 'results': [{'header': {'similarity': '47.43',
                                                                                                 'thumbnail': 'https://img1.saucenao.com/res/pixiv/6967/manga/69676428_p34.jpg?auth=NeUqtRr2AkgAik3tUX-kZQ&exp=1717527600',
                                                                                                 'index_id': 5,
                                                                                                 'index_name': 'Index #5: Pixiv Images - 69676428_p34.jpg',
                                                                                                 'dupes': 0,
                                                                                                 'hidden': 0}, 'data': {
    'ext_urls': ['https://www.pixiv.net/member_illust.php?mode=medium&illust_id=69676428'], 'title': 'モチエロまとめ',
    'pixiv_id': 69676428, 'member_name': '陰茎シャブ昆布', 'member_id': 13290019}}, {'header': {'similarity': '46.63',
                                                                                                'thumbnail': 'https://img3.saucenao.com/furaffinity/3110/31105030.jpg?auth=NlDU2pSwbxseE1Xa9FlXZw&exp=1717527600',
                                                                                                'index_id': 40,
                                                                                                'index_name': 'Index #40: FurAffinity - 31105030.jpg',
                                                                                                'dupes': 0,
                                                                                                'hidden': 0}, 'data': {
    'ext_urls': ['https://www.furaffinity.net/view/31105030'], 'title': 'Possum Sleepy', 'fa_id': 31105030,
    'author_name': 'NatashaArts', 'author_url': 'https://www.furaffinity.net/user/natashaarts'}}, {'header': {
    'similarity': '46.53',
    'thumbnail': 'https://img3.saucenao.com/madokami/Manga/L/LO/LOVE/Love%20in%20the%20Mask/Love%20in%20the%20Mask%20v23%20c95-98.zip/Love_in_the_Mask_v23_c95-98_%5BTinte%5D/Love_in_the_Mask_v23_c98_005.jpg?auth=HvPEEd3Tmw4IUYjkTtmtSQ&exp=1717527600',
    'index_id': 36, 'index_name': 'Index #36: Madokami (Manga) - Love_in_the_Mask_v23_c98_005.jpg', 'dupes': 0,
    'hidden': 0}, 'data': {'ext_urls': ['https://www.mangaupdates.com/series.html?id=48702'], 'mu_id': 48702,
                           'source': 'Love in the Mask', 'part': 'Love in the Mask v23 c95-98', 'type': 'Manga'}}, {
                                                                                         'header': {
                                                                                             'similarity': '46.42',
                                                                                             'thumbnail': 'https://img1.saucenao.com/res/mangadex/770/770146/Q7.jpg?auth=ERuOuQs2r4DOBAUrtTIMnA&exp=1717527600',
                                                                                             'index_id': 37,
                                                                                             'index_name': 'Index #37: MangaDex - Q7.jpg',
                                                                                             'dupes': 0, 'hidden': 0},
                                                                                         'data': {'ext_urls': [
                                                                                             'https://mangadex.org/chapter/4d980735-c4d0-4474-8161-35b1145d0298/'],
                                                                                                  'md_id': '4d980735-c4d0-4474-8161-35b1145d0298',
                                                                                                  'source': 'Suu to Tai-chan',
                                                                                                  'part': ' - Chapter 7',
                                                                                                  'artist': 'Konami Kanata',
                                                                                                  'author': '\ufeffKonami Kanata'}},
                                                                                     {'header': {'similarity': '46.15',
                                                                                                 'thumbnail': 'https://img1.saucenao.com/res/nhentai/58037%20%28339145%29%20--%20%5BLv.%20X%2B%20%28Yuzuki%20N%20Dash%29%5D%20Senjou%20no%20Tsundere%20Buntaichou%20%28Valkyria%20Chronicles%29/34.jpg?auth=WHMQ5A3GxuaRIB3WS2aqCQ&exp=1717527600',
                                                                                                 'index_id': 18,
                                                                                                 'index_name': 'Index #18: H-Misc (nhentai) - 34.jpg',
                                                                                                 'dupes': 0,
                                                                                                 'hidden': 0}, 'data': {
                                                                                         'source': 'Senjou no Tsundere Buntaichou',
                                                                                         'creator': ['yuzuki n dash',
                                                                                                     'lv.x'],
                                                                                         'eng_name': '[Lv. X+ (Yuzuki N Dash)] Senjou no Tsundere Buntaichou (Valkyria Chronicles)',
                                                                                         'jp_name': '戦場のツンデレ分隊長'}}]}


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


def search_img_upload(filename):
    api_key = 'a71bce7cb564ead10b8924be035c34950d97cde2'
    img_url = 'http://39.105.24.101/bot/upload_temp/' + filename
    if not api_key or not img_url:
        raise NotImplementedError('未配置apikey或图片地址')
    target_url = f'https://saucenao.com/search.php?db=999&api_key={api_key}&output_type=2&numres=5&url={img_url}'
    response = requests.get(target_url)
    search_result = response.json()
    retval = {
        'status': 'error',
        'result': None
    }
    if 'results' in search_result:
        retval['status'] = 'success'
        retval['result'] = search_result['results']
    else:
        retval['result'] = 'API返回值没有结果'
    return retval


@app.route('/upload_imgs/<path:authToken>', methods=['POST', 'GET'])
def img_uploader(authToken):
    if authToken != 'fb2a9baab1c23d9786f23ff8708633a63e0e40ff98fa135585ca4491c18193be':
        return flask.render_template('LBY_DONT_HAVE_MOM.html')
    elif authToken == 'Undefined':
        return '你没设置Token'
    if 'image' not in flask.request.files:
        return '没有文件:没有文件'
    file = flask.request.files['image']
    if file.filename == '':
        return '没有文件:没有文件名'
    if file:
        file_content = file.read()
        md5 = hashlib.md5(file_content).hexdigest()
        file.seek(0)  # 重置文件指针
        ext = os.path.splitext(secure_filename(file.filename))[1]  # 获取文件扩展名
        filename = md5 + ext  # 将MD5值和扩展名结合作为文件名
        if not os.path.exists(filename):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        search_result = search_img_upload(filename)
        if search_result['status'] == 'success':
            return str(search_result['result'])
        else:
            return '寄喽' + search_result['result']


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
