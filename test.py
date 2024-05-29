import requests


def req_generate_img():
    api_key = 'sk-mMcHBU7KOAJwfQkOufkdpCrPnoK4t8CQRHmYKTZAs6IfImiN'
    api_key = 'Bearer ' + api_key
    api_url = 'https://p0.kamiya.dev/api/image/generate'
    header = {
        'Authorization': api_key
    }
    data = {
        "type": "text2image",
        "prompts": "礼花，气球，小巷，看着观众，城市，头发飘起，",
        "step": 28,
        "cfg": 12,
        "seed": 218506577,
        "sampling": "DPM++ 2M Karras",
        "width": 768,
        "height": 512,
        "model": "original",
    }
    response = requests.post(api_url, headers=header, json=data, proxies={})
    return response.text


def check_validation():
    api_key = 'sk-mMcHBU7KOAJwfQkOufkdpCrPnoK4t8CQRHmYKTZAs6IfImiN'
    api_key = 'Bearer ' + api_key
    api_url = 'https://p0.kamiya.dev/api/session/getDetails'
    header = {
        'Authorization': api_key
    }
    response = requests.get(api_url, headers=header, proxies={})
    return response.text


if __name__ == '__main__':
    output_type = 'console'
    calling_func = check_validation
    if output_type == 'console':
        print(calling_func())
    elif output_type == 'file':
        with open('output.json', 'w', encoding='utf-8') as file:
            file.write(calling_func())
