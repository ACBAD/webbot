import os
import platform
import requests

def search_img_test():
    api_key = 'a71bce7cb564ead10b8924be035c34950d97cde2'
    img_url = 'https://album.biliimg.com/bfs/new_dyn/42ca4aa3d7595e4034bdde12c46143f2236974553.jpg'
    if not api_key or not img_url:
        raise NotImplementedError('未配置apikey或图片地址')
    target_url = f'https://saucenao.com/search.php?db=999&api_key={api_key}&output_type=2&numres=16&url={img_url}'

    target_url += img_url
    response = requests.get(target_url)

    print(response.status_code)

    with open('output.json', 'w') as file:
        file.write(response.text)

if __name__ == '__main__':
    print(platform.system())
    print(os.path.abspath('.'))
