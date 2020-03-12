import pymysql
from DBUtils.PooledDB import PooledDB
import config.db_config as Config

'''
使用了线程池
'''


class MySQLConnectionPool(object):
    __pool = None  # 设置默认值

    # def __init__(self):
    #     self.conn = self.__getConn();
    #     self.cursor = self.conn.cursor();
    def __enter__(self):
        self.conn = self.__get_connection()
        self.cursor = self.conn.cursor()
        return self

    def __get_connection(self):
        if self.__pool is None:
            self.__pool = PooledDB(creator=pymysql, mincached=Config.DB_MIN_CACHED, maxcached=Config.DB_MAX_CACHED,
                                   maxshared=Config.DB_MAX_SHARED, maxconnections=Config.DB_MAX_CONNECYIONS,
                                   blocking=Config.DB_BLOCKING, maxusage=Config.DB_MAX_USAGE,
                                   setsession=Config.DB_SET_SESSION,
                                   host=Config.DB_TEST_HOST, port=Config.DB_TEST_PORT,
                                   user=Config.DB_TEST_USER, passwd=Config.DB_TEST_PASSWORD,
                                   db=Config.DB_TEST_DBNAME, use_unicode=False, charset=Config.DB_CHARSET)
        return self.__pool.connection()

    def __exit__(self):
        """
        释放资源
        """
        self.cursor.close()
        self.conn.close()

    def getconn(self):
        """
        从线程池取出一个连接
        :return:cursor, conn
        """
        conn = self.__getConn()
        cursor = conn.cursor()
        return cursor, conn
    # 关闭连接归还给连接池
    # def close(self):
    #     self.cursor.close()
    #     self.conn.close()
    #     print("PT连接池释放con和cursor")


def get_connection():
    return MySQLConnectionPool()
