import asyncio
import http.client
import os
from typing import Awaitable
import aiohttp.client_exceptions
import urllib3
from aioconsole import aprint
from pixivpy_async import *


class PixivOAuthError(Exception):
    def __init__(self, message='', interrupted_func: Awaitable = None):
        self.message = message
        self.interrupted_func = interrupted_func
        super().__init__(self.message)


class BetterPixiv:
    def __init__(self, proxy=None, bypass=False):
        self.client = PixivClient(proxy=proxy, bypass=bypass)
        self.api = AppPixivAPI(client=self.client.start(), proxy=proxy, bypass=bypass)
        self.storge_path = os.path.curdir

    async def check_req_validation(self, req: dict, func: Awaitable, user_messages=None):
        if user_messages is None:
            user_messages = []
        if 'error' in req:
            err_msg = req['error']
            if 'user_message' in err_msg and err_msg['user_message']:
                if err_msg['user_message'] == 'Rate Limit':
                    return '请求频率过快'
                for user_message in user_messages:
                    if err_msg['user_message'] == user_message:
                        return user_message
            elif 'message' in err_msg and err_msg['message']:
                if 'Error occurred at the OAuth process.' in err_msg['message']:
                    await aprint('登录失效')
                    await self.api_login(refresh=True)
                    req.clear()
                    req.update(await func)
                    #raise PixivOAuthError('Access token已过期', interrupted_func=func)
            else:
                raise ConnectionRefusedError(f'错误:{req}')
        return ''

    async def api_login(self, refresh_token='', refresh=False):
        if refresh:
            refresh_token = self.api.refresh_token
        if not refresh_token:
            raise PixivOAuthError('未提供refresh_token')
        token = await self.api.login(refresh_token=refresh_token)
        if 'access_token' in token and token['access_token']:
            self.api.set_auth(token['access_token'], refresh_token=refresh_token)
            await aprint('登录成功')
        else:
            raise PixivOAuthError('登录失败')
        return token['access_token']

    async def shutdown(self):
        await self.client.close()
        await aprint('关闭完成')

    def set_storge_path(self, path):
        if os.path.abspath(path):
            self.storge_path = path
        else:
            self.storge_path = os.path.join(os.path.curdir, path)
        if not os.path.exists(self.storge_path):
            try:
                os.makedirs(path, exist_ok=True)
                print('未检测到设置的下载目录，已创建')
            except OSError as e:
                print('目录创建失败，将使用默认目录')

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

    async def multi_download(self, total_work_list: list, thread_num=3) -> list:
        work_lists = BetterPixiv.split_list(total_work_list, thread_num)
        tasks = []
        for work_list in work_lists:
            tasks.append(self.__async_download(work_list))
        pure_results = await asyncio.gather(*tasks)
        return [item for sublist in pure_results for item in sublist]

    async def __async_download(self, work_list: list):
        failed_list = []
        for work in work_list:
            res = await self.download(work)
            if res['total'] == 0 or res['total'] - res['success'] > 0:
                if res['extraInfo'] == '请求频率过快':
                    failed_list = work_list
                    return failed_list
                failed_list.append(work)
        return failed_list

    async def download(self, inner_work_id, sudo=False) -> dict:
        await asyncio.sleep(1)
        await aprint(f'正在下载{inner_work_id}')
        dl_result = {'total': 0, 'success': 0, 'paths': [], 'extraInfo': ''}
        work_details = await self.api.illust_detail(inner_work_id)
        validation = await self.check_req_validation(work_details, self.api.illust_detail(inner_work_id),
                                                     user_messages=['ページが見つかりませんでした'])
        if validation:
            dl_result['extraInfo'] = validation
            return dl_result

        '''if 'error' in work_details:
            err_msg = work_details['error']
            if 'user_message' in err_msg and err_msg['user_message']:
                if err_msg['user_message'] == 'Rate Limit':
                    dl_result['extraInfo'] = '请求频率过快'
                    return dl_result
                elif err_msg['user_message'] == 'ページが見つかりませんでした':
                    dl_result['extraInfo'] = '你所请求的作品不存在'
                    return dl_result
            elif 'message' in err_msg and err_msg['message']:
                if err_msg['message'] == 'Error occurred at the OAuth process. Please check your Access Token to fix this. Error Message: invalid_grant':
                    raise PixivOAuthError('Access token已过期', interrupted_func=self.download(inner_work_id))
            else:
                raise ConnectionRefusedError(f'错误:{work_details}')'''

        if work_details['illust']['meta_pages']:
            work_url_list = [cop["image_urls"]["original"] for cop in work_details['illust']['meta_pages']]
            dl_result['total'] = len(work_url_list)
            if not sudo:
                if len(work_url_list) > 10:
                    dl_result['success'] = 0
                    dl_result['extraInfo'] = 'Exceed Limit'
                    return dl_result
            for url in work_url_list:
                multi_img_name = url.split('/')[-1]
                multi_img_path = os.path.join(self.storge_path, multi_img_name)
                if os.path.exists(multi_img_path):
                    dl_result['success'] += 1
                    dl_result['paths'].append(multi_img_name)
                    continue
                for cnt in range(10):
                    try:
                        await asyncio.sleep(1)
                        await self.api.download(url, path=self.storge_path)
                        dl_result['success'] += 1
                        dl_result['paths'].append(multi_img_name)
                        break
                    except asyncio.exceptions.TimeoutError:
                        await aprint(f'下载{inner_work_id}时出错，尝试重试，当前次数{cnt + 1}')
                        try:
                            os.remove(multi_img_path)
                        except FileNotFoundError:
                            pass
                    except aiohttp.client_exceptions.ServerDisconnectedError:
                        await aprint(f'下载{inner_work_id}时出错，尝试重试，当前次数{cnt + 1}')
                        try:
                            os.remove(multi_img_path)
                        except FileNotFoundError:
                            pass
                    except http.client.IncompleteRead:
                        await aprint(f'下载{inner_work_id}时出错，尝试重试，当前次数{cnt + 1}')
                        try:
                            os.remove(multi_img_path)
                        except FileNotFoundError:
                            pass
                    except urllib3.exceptions.ProtocolError:
                        pass
                    if cnt == 10:
                        await aprint(f'{inner_work_id}下载失败, 已达重试次数上限, 已成功{dl_result["success"]}个')
                        return dl_result
            return dl_result
        elif work_details['illust']['meta_single_page']:
            img_url: str = work_details['illust']['meta_single_page']['original_image_url']
            img_name = img_url.split('/')[-1]
            img_path = os.path.join(self.storge_path, img_name)
            dl_result['total'] = 1
            if os.path.exists(img_path):
                dl_result['success'] = 1
                dl_result['paths'].append(img_name)
                return dl_result
            for cnt in range(10):
                try:
                    await asyncio.sleep(1)
                    await self.api.download(img_url, path=self.storge_path)
                    dl_result['success'] = 1
                    dl_result['paths'] = [img_name]
                    return dl_result
                except asyncio.exceptions.TimeoutError:
                    await aprint(f'下载{inner_work_id}时出错，尝试重试，当前次数{cnt + 1}')
                    try:
                        os.remove(img_path)
                    except FileNotFoundError:
                        pass
                except aiohttp.client_exceptions.ServerDisconnectedError:
                    await aprint(f'下载{inner_work_id}时出错，尝试重试，当前次数{cnt + 1}')
                    try:
                        os.remove(img_path)
                    except FileNotFoundError:
                        pass
                except http.client.IncompleteRead:
                    await aprint(f'下载{inner_work_id}时出错，尝试重试，当前次数{cnt + 1}')
                    try:
                        os.remove(img_path)
                    except FileNotFoundError:
                        pass
                except urllib3.exceptions.ProtocolError:
                    pass
            await aprint(f'下载{inner_work_id}失败，已达重试次数上限')
            return dl_result

    async def get_user_works(self, user_id: int) -> list:
        user_works = await self.api.user_illusts(user_id)
        validation = await self.check_req_validation(user_works, self.api.user_illusts(user_id))
        if validation:
            await aprint(validation)
            return []
        return [work['id'] for work in user_works['illusts']]

    async def get_favs(self, user_id=88725668) -> list:
        fav_list = []
        max_mark = None
        try:
            while True:
                favs = await self.api.user_bookmarks_illust(user_id, max_bookmark_id=max_mark)
                validation = await self.check_req_validation(favs, self.api.user_bookmarks_illust(user_id, max_bookmark_id=max_mark))
                if validation:
                    await aprint(validation)
                    return []
                next_url: str = favs['next_url']
                if not next_url:
                    return fav_list
                index = next_url.find('max_bookmark_id=') + len('max_bookmark_id=')
                max_mark = next_url[index:]
                fav_list += [work['id'] for work in favs['illusts']]
                await asyncio.sleep(0.5)
        except KeyError:
            return fav_list

    async def use_id_check_exsit(self, inner_work_id):
        name_list = [f'{inner_work_id}_p0.png', f'{inner_work_id}_p0.jpg',
                     f'{inner_work_id}.jpg', f'{inner_work_id}.png',
                     f'{inner_work_id}_0.png', f'{inner_work_id}_0.jpg']
        cnt = 0
        for name in name_list:
            if os.path.exists(os.path.join(self.storge_path, name)):
                cnt += 1
        return cnt

    async def get_nolocal_works(self, user_id=88725668):
        max_mark = None
        nolocal_list = []
        try:
            while True:
                favs = await self.api.user_bookmarks_illust(user_id, max_bookmark_id=max_mark)
                validation = await self.check_req_validation(favs, self.api.user_bookmarks_illust(user_id, max_bookmark_id=max_mark))
                if validation:
                    await aprint(validation)
                    return []
                fmt_favs = [work['id'] for work in favs['illusts']]
                for work in fmt_favs:
                    if await self.use_id_check_exsit(work):
                        return nolocal_list
                    else:
                        nolocal_list.append(work)
                next_url: str = favs['next_url']
                if not next_url:
                    return nolocal_list
                index = next_url.find('max_bookmark_id=') + len('max_bookmark_id=')
                max_mark = next_url[index:]
                await asyncio.sleep(0.5)
        except KeyError:
            return nolocal_list

    async def get_new_works(self):
        work_list = await self.api.illust_follow(req_auth=True)
        validation = await self.check_req_validation(work_list, self.api.illust_follow(req_auth=True))
        if validation:
            await aprint(f'validation:{validation}')
            return []
        try:
            return [work['id'] for work in work_list['illusts']]
        except KeyError:
            return [work_list]


if __name__ == '__main__':
    async def test():
        api = BetterPixiv(proxy='http://127.0.0.1:10809')
        await api.api_login(refresh_token='a4TF-gC5kRkciAiZ5MhGUoVw6zb3AXO1M1DmnAeFGlk')
        await aprint(await api.download(99905230523))
        await api.shutdown()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
