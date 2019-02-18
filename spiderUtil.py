import requests
import os
import logging
import requests
from contextlib import closing
import time


class spiderUtil():


    def __init__(self,logger):
        self.logger = logger

    def set_logger(self, logger):
        self.logger = logger

    def get_url(self, opener, url, formdata = None, time = 3):
        maxTryNum = time
        for tries in range(maxTryNum):
            try:
                if formdata:
                    html = opener.open(url, formdata).read().decode("utf-8")
                else:
                    html = opener.open(url).read().decode("utf-8")
                break
            except Exception as e:
                if tries < maxTryNum:
                    continue
                else:
                    self.logger.error("Has tried %d times to access url %s, all failed! 异常是 %s", maxTryNum, url, repr(e))
                    break
            maxTryNum -= 1
        return html

    # 下载图片
    def download(self, imgUrl, savePath, header=None):
        try:
            img_name = imgUrl.split("/")[-1]
            full_path = savePath + img_name
            if os.path.exists(full_path):
                self.logger.debug("已存在该图片，保存在" + full_path + "。url是" + imgUrl)
                return True
            else:
                return self.downimgs(imgUrl, full_path, header)
        except:
            raise

    def downimgs(self, url, save_path, header):
        '''
        根据url下载图片，成功就返回True
        :param url:
        :param save_path:
        :param header:
        :return:
        '''
        try:
            with closing(requests.get(url, verify=False, stream=True, headers=header)) as r:
                if r.status_code != 404:
                    with open(save_path, 'wb') as f:
                        for data in r.iter_content(1024):
                            if data:
                                f.write(data)
                else:
                    self.logger.error("找不图片,url地址是" + url)
            return True
        except Exception as e:
            raise

    def save_img(self, response, save_path):
        f = open(save_path, 'wb')  # 打开文件
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()
        f.close()

    def write2file(filename, content, encoding="utf-8"):
        f = open(filename, "w", encoding=encoding)
        f.write(content)
        f.close()