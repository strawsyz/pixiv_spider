# import imageio
import zipfile
import os
import requests
from contextlib import closing
import time
from deprecated import deprecated
# from ugoira import lib as ugoira
from utils.log_util import Log
from utils.file_util import make_directory
import utils.file_util


class SpiderUtil:
    def __init__(self, header=None, proxies=None):
        self.logger = Log(__name__).get_log()
        self.header = header
        self.proxies = proxies
        # 防止证书警告显示
        requests.packages.urllib3.disable_warnings()

    def set_header(self, header):
        self.header = header

    def download_img(self, img_url, save_path, header=None):
        """
        下载一张图片，如果本地有一张该图片，且图片内容完整，就不下载
        """
        try:
            img_name = img_url.split("/")[-1]
            full_path = os.path.join(save_path, img_name)
            if os.path.exists(full_path) and file_util.valid_file(full_path):
                self.logger.debug("已存在该图片，保存在" + full_path + "。url是" + img_url)
                return True
            else:
                return self.download_file(img_url, full_path, headers=header)
        except Exception as e:
            raise e

    def download_file(self, url, save_path, headers=None, proxies=None, time_out=16, chunk_size=1024000):
        """
        根据url下载文件，成功就返回True
        不属于requests部分的代码只会运行try_time次
        time_out的单位可能是分
        :param url: 请求的url
        :param save_path:  文件保存的位置
        :param headers:  请求时使用的头
        :param proxies:  代理
        :param time_out:  超时的时间
        :param chunk_size:  下载的缓存的大小
        :return: 没有找到文件，返回404，下载成功返回True 否则返回False
        """
        try:
            (header, proxies) = self.prepare(headers, proxies)
            with closing(requests.get(url, verify=False, stream=True, headers=header, proxies=proxies,
                                      timeout=time_out)) as r:
                if r.status_code != 404:
                    with open(save_path, 'wb') as f:
                        for data in r.iter_content(chunk_size):
                            if data:
                                f.write(data)
                    self.logger.info('download successful {}'.format(url))
                else:
                    self.logger.error("cannot find file, url is {}".format(url), exc_info=True)
                    return False
            return True
        except Exception as e:
            # raise e
            # time.sleep(60)
            # 若是最后一次报错，就打日志
            self.logger.error("some problems happened while downloading file, url is {}".format(url), exc_info=True)
            # if try_times > 1:
            #     try_times = try_times - 1
            #     return self.download_file(url, save_path, headers=headers, proxies=proxies, chunk_size=chunk_size,
            #                               try_times=try_times)
            return False

    def easy_download_file(self, url, save_path, chunk_size=1024000):
        """
       没有缓存机制，很简单，但是下载大文件有可能失败,而且比较占内存
       直接返回content
        """
        # try:
        with closing(requests.get(url, verify=False, stream=True)) as r:
            if r.status_code != 404:
                with open(save_path, 'wb') as f:
                    for data in r.iter_content(chunk_size):
                        if data:
                            f.write(data)
                self.logger.info('download successful {}'.format(url))
            else:
                self.logger.error("cannot find file, url is {}".format(url), exc_info=True)
                return 404
        # return requests.get(url, verify=False, stream=True, headers=headers).content
        # except Exception as e:
        #     if try_times >= 0:
        #         return self.easy_download_file(url, headers, --try_times)
        #     self.logger.error("cannot download file, url is {}".format(url), exc_info=True)
        #     return False

    def post(self, url, data=None, header=None, proxies=None):
        (header, proxies) = self.prepare(header, proxies)
        r = requests.post(url, headers=header, proxies=proxies, data=data)
        return r

    def json(self, url, header=None, proxies=None, except_code=None):
        """
        如果response的code是属于可以接受的code
        就解析返回的json，最后return出去
        """
        (header, proxies) = self.prepare(header, proxies)
        response = requests.get(url, headers=header, proxies=proxies)
        if response.status_code == except_code:
            return response.json()
        else:
            return None

    @staticmethod
    def json(url, session, except_code=None):
        response = session.get(url)
        print(response.text)
        if response.status_code == except_code:
            return response.json()
        else:
            return None

    def save_html(self, url, path, header=None, proxies=None, encoding='utf-8'):
        """
        将html页面保存在文件中，用于简单的测试
        """
        try:
            (header, proxies) = self.prepare(header, proxies)
            r = requests.get(url, headers=header, proxies=proxies).text
            with open(path, 'w', encoding=encoding) as f:
                f.write(r)
        except Exception as e:
            raise e

    # def download_ugoira(self, zip_url, frames, gif_path, zip_path, headers=None, speed=1.0):
    #     """
    #      下载ugoira文件
    #     下载数据之后直接保存在gif中
    #     :param zip_url: zip的url
    #     :param frames: frames信息
    #     :param gif_path: gif保存位置
    #     :param zip_path: zip下载路径
    #     :param headers: 下载zip文件的请求头
    #     :param speed: 控制图片间的间隔
    #     :return:
    #     """
    #     # 下载content的内容
    #     zip_content = self.easy_download_file(zip_url, headers=headers, try_times=5)
    #     if zip_content is False:
    #         return False
    #     # ugoira.save('zip', zip_path, zip_content, frames, speed)
    #     # 保存为gif
    #     # ugoira.save(format, gif_path, zip_content, frames, speed)
    #     return False

    def download_ugoira(self, url, zip_path, headers=None):
        """
        没有使用ugoira的下载
        先把zip下载到本地
        再本地解压，再组成gif
        最后删去解压产生的jpg文件
        """
        try:
            # 下载zip文件，获得文件信息
            # zip_path = os.path.join(dest, illust_id + ".zip")
            # 下载content的内容
            return self.download_file(url, zip_path, headers=headers)
        except Exception as e:
            self.logger.error('动图下载失败,{} is '.format(url), exc_info=True)
            # raise e
            return False

    # def my_download_ugoira(self, url, frames, dest, illust_id: str, delays, headers=None):
    #     """
    #     没有使用ugoira的下载
    #     先把zip下载到本地
    #     再本地解压，再组成gif
    #     最后删去解压产生的jpg文件
    #     """
    #     try:
    #         # 下载zip文件，获得文件信息
    #         zip_path = os.path.join(dest, illust_id + ".zip")
    #         # 下载content的内容
    #         zipp = self.download_file(url, zip_path, headers=headers)
    #         # gif_data = gif_data.content
    #         file_path = os.path.join(dest, illust_id)
    #         make_directory(file_path)
    #         temp_file_list = []
    #         zipo = zipfile.ZipFile(zip_path, "r")
    #         for file in zipo.namelist():
    #             temp_file_list.append(os.path.join(file_path, file))
    #             zipo.extract(file, file_path)
    #         zipo.close()
    #         # 读取所有静态图片，合成gif
    #         image_data = []
    #         for file in temp_file_list:
    #             image_data.append(imageio.imread(file))
    #         # ValueError: Image is not numeric, but
    #         # Array.
    #         # 第二种报错    ValueError: quantization error
    #         imageio.mimsave(os.path.join(file_path, illust_id + ".gif"), image_data, "GIF", duration=delays)
    #         # 清除所有中间文件。
    #         for file in temp_file_list:
    #             os.remove(file)
    #         return True
    #     except Exception as e:
    #         self.logger.error('动图下载，转化为gif失败,illust_id is ' + illust_id, exc_info=True)
    #         raise e

    def download_resume(self, url, file_path, headers=None, chunk_size=1024000):
        """支持断点续传的文件下载方式"""
        try:
            temp = requests.get(url, stream=True, verify=False, headers=headers)
            # 获得文件大小
            total_size = int(temp.headers['Content-Length'])
            self.logger.info('文件总大小为 ', total_size)
            # 这重要了，先看看本地文件下载了多少
            if os.path.exists(file_path):
                temp_size = os.path.getsize(file_path)  # 本地已经下载的文件大小
            else:
                temp_size = 0
            self.logger.info('已下载文件大小为 ', temp_size)
            # 设置下载范围
            headers = {'Range': 'bytes=%d-' % temp_size}
            # 重新请求网址，加入新的请求头的
            r = requests.get(url, stream=True, verify=False, headers=headers)

            # "ab"表示追加形式写入文件
            with open(file_path, "ab") as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        temp_size += len(chunk)
                        f.write(chunk)
                        f.flush()
                        done = int(50 * temp_size / total_size)
                        # 输出进度条
                        self.logger.info(
                            "\r[%s%s] %d%%" % ('█' * done, ' ' * (50 - done), 100 * temp_size / total_size))
            self.logger.info("done")
            return True
        except Exception as e:
            self.logger.info('改文件可能不支持断点续传')
            return False

    def download_aira(self, url, dest_path):
        pass

    def prepare(self, header=None, proxies=None):
        if header is None:
            header = self.header
        if proxies is None:
            proxies = self.proxies
        return header, proxies

    def is_support_continue(self, url, headers={}):
        """判断是否支持断点续传、多线程下载"""
        headers['Range'] = 'bytes=0-4'
        # noinspection PyBroadException
        try:
            r = requests.head(url, headers=headers)
            crange = r.headers['content-range']
            import re
            int(re.match(r'^bytes 0-4/(\d+)$', crange).group(1))
            return True
        except Exception:
            return False


if __name__ == '__main__':
    util = SpiderUtil()
    # url = 'http://n9.1whour.com/newkuku/2017/03/09/鬼灭之刃_第51话/00130PB.jpg'
    url = 'https://pic1.zhimg.com/v2-2b5a13bac4a614f1bf2d05172db63b86_1200x500.jpg'
    util.easy_download_file(url, 'temp.jpg')

    pass
    util = SpiderUtil()
    header = {'Referer': "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index",
              'User-Agent': 'User-Agent:Mozilla/5.0',
              # 'cookie':'first_visit_datetime_pc=2018-09-07+00%3A33%3A54; p_ab_id=3; p_ab_id_2=4; __guid=68439831.2211692229076777700.1536248022797.7734; privacy_policy_agreement=1; a_type=0; b_type=1; login_ever=yes; p_ab_d_id=300550071; yuid_b=F3MniSk; OX_plg=swf|sl|wmp|shk|pm; PHPSESSID=16921928_c52c2cc9a3c1567ded91e0c34c998713; device_token=eb457ae7d6a38a72efc65e7a59edb685; c_type=22; limited_ads=%7B%22responsive%22%3A%22%22%7D; categorized_tags=0KixsJBDVn~BU9SQkS-zU~NgHIkiGFP2~OEXgaiEbRa~b8b4-hqot7~uQ8dUM2bls; monitor_count=2; tag_view_ranking=q3eUobDMJW~RTJMXD26Ak~BU9SQkS-zU~y8GNntYHsi~O6hKA9LFUP~NpsIVvS-GF~GI4GuwP6yD~mu7939gcfy~P8cnvSyzik~kP7msdIeEU~YX3tU8uRAA~bPI9qoWvsg'
              }
    url = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=74724305'
    url = 'https://i.pximg.net/imgaz/2019/03/22/10/34/21/contest_icon_266.png'
    util.download_file('https://www.pixiv.net/ranking.php?mode=daily&content=illust', '1.gif')
    util.download_file(url, '3.png', headers=header)
    # url = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=74735185'
    # util.save_html(url, '3.html')
    # session
