import jmcomic
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import platform
if platform.system() == 'Windows':
    from selenium.webdriver.edge.options import Options
else:
    from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class jm_tankobon:
    def __init__(self):
        jmcomic.disable_jm_log()
        self.client = jmcomic.JmOption.default().new_jm_client()
        print('jm模块载入完成')

    @staticmethod
    def format_name(raw_str) -> str:
        converted_str = ''
        in_bracket = 0
        for c in raw_str:
            if c in [']', '}', ')', '】', '）', '］']:
                in_bracket -= 1
                continue
            elif c in ['[', '{', '【', '(', '（', '［']:
                in_bracket += 1
                continue
            elif c == ' ':
                continue
            if not in_bracket:
                converted_str += c
            else:
                continue
        return converted_str

    def get_origin_name(self, jmid):
        jmid = str(jmid)
        page = self.client.search_site(search_query=jmid)
        if hasattr(page, 'album'):
            album: jmcomic.JmAlbumDetail = page.single_album
            return album.title
        else:
            print('无法解析的JM号')
            return ''

    def get_pure_name(self, jmid):
        return self.format_name(self.get_origin_name(jmid))

    def get_hitomi_url(self, jmid=0, bon_title=''):
        download_url = ''
        if jmid:
            bon_title = self.get_pure_name(jmid)
        if not bon_title:
            print('无法获取下载URL:本名为空')
            return ''
        else:
            browser_options = Options()
            browser_options.add_argument('--headless')
            browser_options.add_argument('--disable-gpu')
            browser_options.add_argument('--no-sandbox')
            target_url = f'https://hitomi.la/search.html?{bon_title} language:chinese'
            print('请求构造完成')
            if platform.system() == 'Windows':
                driver = webdriver.Edge(options=browser_options)
            else:
                driver = webdriver.Firefox(options=browser_options)
            wait = WebDriverWait(driver, 15)
            try:
                driver.get(target_url)
                print('启动浏览器')
                print('等待搜索结果')
                wait_filled = lambda inner_driver: inner_driver.find_element(By.CLASS_NAME,
                                                                             "gallery-content").text.strip() != ''
                wait.until(wait_filled)
                search_result_element = driver.find_element(By.CLASS_NAME, "gallery-content")
                main_search_page = driver.current_window_handle
                print('已加载搜索结果')
                tankobons_element = search_result_element.find_elements(By.XPATH, ".//*")
                if not tankobons_element:
                    print('无结果')
                    return
                tankobon_element = tankobons_element[0]
                if tankobon_element.text == 'No Results':
                    print('无结果')
                    return
                link_element = tankobon_element.find_elements(By.XPATH, ".//h1[@class='lillie']/a")[0]
                link_element.click()
                print('点击第一个结果')
                print('等待本子加载')
                download_button_element = wait.until(EC.presence_of_element_located((By.XPATH,
                                                                                     "//body/div[@class='container']/div[@class='content']/div[@class='cover-column lillie']/a[@id='dl-button']")))

                bon_title = wait.until((EC.presence_of_element_located((By.XPATH,
                                                                        "//body/div[@class='container']/div[@class='content']/div[starts-with(@class, 'gallery')]/h1[@id='gallery-brand']/a"))))
                bon_title = bon_title.text
                download_url = driver.current_url
            except TimeoutException:
                print('元素等待超时，退出')
            finally:
                driver.quit()
                return download_url

if __name__ == '__main__':
    jm_api = jm_tankobon()
    pure_name = jm_api.get_origin_name(551278)
    print(pure_name)
    print(jm_api.format_name(pure_name))
    print(jm_api.get_hitomi_url(bon_title=jm_api.format_name(pure_name)))
