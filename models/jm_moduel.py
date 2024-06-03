import jmcomic


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
            print(f'无法解析的JM号{jmid}')
            return ''

    def get_pure_name(self, jmid):
        return self.format_name(self.get_origin_name(jmid))
