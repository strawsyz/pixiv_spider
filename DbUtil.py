import pymysql

class DbUtil():
    #初始化方法
    def __init__(self, host,  user, passwd, db_name, charsets):
        self.host = host
        # self.port = port
        self.user = user
        self.passwd = passwd
        self.dbName = db_name
        self.charsets = charsets

    # 连接数据库
    def getCon(self):
        self.db = pymysql.Connect(
            host=self.host,
            # port=self.port,
            user=self.user,
            passwd=self.passwd,
            db=self.dbName,
            charset=self.charsets
        )
        self.cursor = self.db.cursor()

    #关闭链接
    def close(self):
        self.cursor.close()
        self.db.close()

    #查询单行记录
    def get_one(self, sql):
        res = None
        try:
            self.getCon()
            self.cursor.execute(sql)
            res = self.cursor.fetchone()
        except:
            print("查询失败!"+sql)
        return res

    #查询列表数据
    def get_all(self, sql):
        res = None
        try:
            self.getCon()
            self.cursor.execute(sql)
            res = self.cursor.fetchall()
            self.close()
        except:
            print("查询失败！"+sql)
        return res

    # 执行语句
    def __execute(self, sql):
        count = 0
        try:
            self.getCon()
            count = self.cursor.execute(sql)
            self.db.commit()
            self.close()
        except:
            print("操作失败！"+sql)
            self.db.rollback()
        return count

        # 修改数据
    def insert(self, sql):
        return self.__execute(sql)

    #修改数据
    def edit(self, sql):
        return self.__execute(sql)

    #删除数据
    def delete(self, sql):
        return self.__execute(sql)

    #更新数据
    def update(self, sql):
        return self.__execute(sql)
if __name__ == '__main__':
    bd_util = DbUtil("localhost", "root", "straw@syz", "test", "utf8")
    res = bd_util.get_one("select * from illust where illust_id = "+ "214212 "+" and status = 10")
    if res:
        print(12)