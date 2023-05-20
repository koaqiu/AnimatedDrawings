import oss2
import utils
import datetime
import os

class OssClient(object):
    def __init__(self, config) -> None:
        self.config = config
        self.client = self.setupOss()

    def setupOss(self):
        config = self.config
        # 阿里云账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM用户进行API访问或日常运维，请登录RAM控制台创建RAM用户。
        auth = oss2.Auth(config.get('access_key_id'), config.get('access_key_secret'))
        # 填写自定义域名，例如example.com。
        cname = config.get('cname')
        bucketName = config.get('bucket')
        # 填写Bucket名称，并设置is_cname=True来开启CNAME。CNAME是指将自定义域名绑定到存储空间。
        bucket = oss2.Bucket(auth, cname, bucketName, is_cname=config.get('useCName'))
        return bucket


    def uploadToOss(self, localFile):
        """
        上传文件到OSS。
        返回可访问的url
        """
        bucket = self.client
        print("上传图片到OSS")
        ossKey = (
            "ad/"
            + (datetime.datetime.now().strftime("%Y/%m%d/%H"))
            + "/"
            + (localFile.split(os.sep).pop())
        )
        bucket.put_object_from_file(ossKey, localFile)
        return self.cname + "/" + ossKey
