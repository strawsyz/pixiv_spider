import os
import zipfile36 as zipfile
from PIL import Image


def make_directory(dir_name):
    """判断文件夹是否存在，如果不存在就新建文件夹"""
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, mode=0o777)


# 以下方法可以判断jpg图片是否完整
def is_valid_jpg(jpg_file):
    try:
        with open(jpg_file, 'rb') as f:
            # seek() 方法用于移动文件读取指针到指定位置。
            # offset -- 开始的偏移量，也就是代表需要移动偏移的字节数
            # whence：可选，默认值为 0。给offset参数一个定义，表示要从哪个位置开始偏移；
            # 0代表从文件开头开始算起，1代表从当前位置开始算起，2代表从文件末尾算起。
            f.seek(-2, 2)
            buf = f.read()
            f.close()
            return buf == b'\xff\xd9'  # 判定jpg是否包含结束字段
    except Exception as e:
        raise e


def is_valid_png(png_file):
    try:
        with open(png_file, 'rb') as f:
            f.seek(-8, 2)
            buf = f.read()
            f.close()
            return buf == b'IEND\xaeB`\x82'
    except Exception as e:
        raise e


def is_valid_zip(zip_file):
    try:
        zipfile.ZipFile(zip_file)  # 能检测文件是否完整
        # return z_file.testzip()  # 测试能否解压zip文件
        return True
    except zipfile.BadZipFile as e:
        return False
    except Exception as e:
        # from logger import Log
        # logger = Log(__name__).get_log()
        # logger.error('trouble in zip_file ', exc_info=True)
        print('trouble in zip_file {}'.format(zip_file))
        raise e


def valid_file(file_path, file_type: str = None):
    file_type = file_extension(file_path) if file_type is None else file_type
    if file_type == '.jpg':
        return is_valid_jpg(file_path)
    elif file_type == '.png':
        return is_valid_png(file_path)
    elif file_type == '.zip':
        return is_valid_zip(file_path)
    else:
        raise NotImplementedError("还不支持{}格式,文件在{}".format((file_type, file_path)))


def file_extension(path):
    """获得文件的后缀名"""
    return os.path.splitext(path)[1]


def valid_file_batch(root_path, recursive=False):
    """判断文件夹下的所有文件的完整性"""
    for file in os.listdir(root_path):
        path = os.path.join(root_path, file)
        if os.path.isdir(path) and recursive:
            valid_file_batch(path)
        else:
            extension = file_extension(file)
            res = valid_file(path, extension)
            if not res:
                print('this file is incomplete {}'.format(path))


def batch_img2thumbnail(file_dir, size, dest_dir=None, ignore=[]):
    if dest_dir is None:
        dest_dir = os.path.join(file_dir, 'thumbnail')  # pixiv/thumbnail
    for file in os.listdir(file_dir):
        if file in ignore:
            continue
        path = os.path.join(file_dir, file)
        if os.path.isdir(path):  # pixiv/12321/
            if path != dest_dir:
                batch_img2thumbnail(path, size, os.path.join(dest_dir, file))  # pixiv/thumbnail/12321/
            else:
                continue
        else:
            # 防止win中自动生成的缩略图文件被处理
            if file == 'Thumbs.db':
                continue
            img2thumbnail(path, os.path.join(dest_dir, file), size)


def img2thumbnail(file_path, dest_path, size, is_cover=False):
    # 若文件存在且不覆盖，则跳出
    if os.path.exists(dest_path) and not is_cover:
        return
    # 文件后缀名检查
    ext = file_extension(file_path)
    if ext not in [".jpg", ".png"]:
        return
    if not os.path.exists(file_path):
        print('找不到图片，请重新检查路径{}'.format(file_path))
        return
    if not valid_file(file_path, ext):
        return
    make_directory(os.path.dirname(dest_path))
    try:
        im = Image.open(file_path)
        im.thumbnail(size)
        im.save(dest_path)
        print(file_path)
    except OSError:
        print('{} 文件有问题'.format(file_path))


def get_cur_dir(py_file):
    return os.path.dirname(os.path.abspath(py_file))  # 当前py文件所在的路径


# if __name__ == '__main__':
#     valid_file_batch('D:/pixiv/download')
# files = os.listdir('D:/pixiv/download')
# for file in files:
#     if os.path.isdir(files):
#         pass
#     else:
#         path = os.path.join(root_path, file)
#         extension = file_extension(file)
#         valid_file(file, extension)

if __name__ == '__main__':
    # batch_img2thumbnail('D:\Temp\收藏', (300, 400))
    # print("ok")

    print(get_cur_dir(__file__))