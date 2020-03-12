from fake_useragent import UserAgent

"""给爬虫设置header"""


def get_header(host):
    if host == 'pixiv':
        return {
            'Referer': "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index",
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
        }
    else:
        return {}


class HeaderUtil():
    def __init__(self):
        self.user_agent = UserAgent()
        self.user_agent_4_pixiv = {}
        pass

    def get_random_user_agent(self):
        return self.user_agent.random

    def get_user_agent(self, type):
        if type == 'chrome':
            return self.user_agent.chrome
        if type == 'ie':
            return self.user_agent.ie
        if type == 'firefox':
            return self.user_agent.firefox
        if type == 'safari':
            return self.user_agent.safari
        if type == 'opera':
            return self.user_agent.opera
