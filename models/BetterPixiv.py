import http.client
import os
import time
from typing import Any
import pixivpy3
import urllib3


class BetterPixiv(pixivpy3.AppPixivAPI):
    def __init__(self, formal_refresh_token, formal_access_token=None, **kwargs: Any):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        super().__init__(**kwargs)
        self.refresh_token = formal_refresh_token
        self.access_token = formal_access_token
        self.token_ability = True
        self.storge_path = os.path.curdir
        self.auth(refresh_token=self.refresh_token)
        print('初始化完成')

    def set_storge_path(self, path):
        if os.path.abspath(path):
            self.storge_path = path
        else:
            self.storge_path = os.path.join(os.path.curdir, path)
        if not os.path.exists(self.storge_path):
            raise FileNotFoundError('设置的下载路径不存在')

    def use_id_check_exsit(self, inner_work_id):
        name_list = [f'{inner_work_id}_p0.png', f'{inner_work_id}_p0.jpg', f'{inner_work_id}.jpg', f'{inner_work_id}.png', f'{inner_work_id}_0.png', f'{inner_work_id}_0.jpg']
        cnt = 0
        for name in name_list:
            if os.path.exists(os.path.join(self.storge_path, name)):
                cnt += 1
        return cnt

    @staticmethod
    def split_list(lst, num_parts):
        # 计算每个部分的长度
        total_length = len(lst)
        part_length = total_length // num_parts
        remainder = total_length % num_parts
        # 初始化切分后的部分列表
        parts = []
        # 切分列表
        start = 0
        for i in range(num_parts):
            # 计算当前部分的长度
            length = part_length + (1 if i < remainder else 0)
            # 切分当前部分并添加到部分列表中
            parts.append(lst[start:start + length])
            # 更新起始位置
            start += length
        return parts

    def download(self, inner_work_id, **kwargs) -> list:
        work_details = self.illust_detail(inner_work_id)
        time.sleep(0.5)
        if 'error' in work_details:
            if 'user_message' in work_details:
                print(f'错误:{work_details["user_message"]}')
            else:
                print(f'错误:{work_details["error"]}')
            return []

        if work_details['illust']['meta_pages']:
            work_url_list = [cop["image_urls"]["original"] for cop in work_details['illust']['meta_pages']]
            success_list = []
            for url in work_url_list:
                multi_img_name = url.split('/')[-1]
                multi_img_path = os.path.join(self.storge_path, multi_img_name)
                if os.path.exists(multi_img_path):
                    success_list.append(multi_img_name)
                    continue
                for cnt in range(11):
                    try:
                        time.sleep(1)
                        if super().download(url, path=self.storge_path):
                            success_list.append(multi_img_name)
                            break
                    except http.client.IncompleteRead:
                        print(f'下载{inner_work_id}时出错，尝试重试，当前次数{cnt + 1}')
                        try:
                            os.remove(multi_img_path)
                        except FileNotFoundError:
                            pass
                    except urllib3.exceptions.ProtocolError:
                        pass
                    if cnt == 10:
                        print(f'{inner_work_id}下载失败, 已达重试次数上限, 已成功{len(success_list)}个')
                        return success_list
            return success_list
        elif work_details['illust']['meta_single_page']:
            img_url: str = work_details['illust']['meta_single_page']['original_image_url']
            img_name = img_url.split('/')[-1]
            img_path = os.path.join(self.storge_path, img_name)
            if os.path.exists(img_path):
                return [img_name]
            for cnt in range(10):
                try:
                    time.sleep(1)
                    if super().download(img_url, path=self.storge_path):
                        return [img_name]
                    else:
                        return []
                except http.client.IncompleteRead:
                    print(f'下载{inner_work_id}时出错，尝试重试，当前次数{cnt + 1}')
                    try:
                        os.remove(img_path)
                    except FileNotFoundError:
                        pass
                except urllib3.exceptions.ProtocolError:
                    pass
            print(f'下载{inner_work_id}失败，已达重试次数上限')
            return []

    def get_user_works(self, user_id: int) -> list:
        return [work['id'] for work in self.user_illusts(user_id)['illusts']]

    def get_favs(self, user_id=88725668) -> list:
        fav_list = []
        max_mark = None
        try:
            while True:
                favs = self.user_bookmarks_illust(user_id, max_bookmark_id=max_mark)
                next_url: str = favs['next_url']
                index = next_url.find('max_bookmark_id=') + len('max_bookmark_id=')
                max_mark = next_url[index:]
                fav_list += [work['id'] for work in favs['illusts']]
                time.sleep(0.5)
        except KeyError:
            return fav_list

if __name__ == '__main__':
    li = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(BetterPixiv.split_list(li, 3))
