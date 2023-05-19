from flask_restful import Api, Resource, request
from flask import send_from_directory
import json
import yaml
import datetime
import uuid
import os
import tempfile
import requests
from pathlib import Path
from http import HTTPStatus
from examples.annotations_to_animation import annotations_to_animation
from examples.image_to_annotations import image_to_annotations
from pkg_resources import resource_filename
import oss2


def resourcePath(path:str):
    return os.path.abspath(resource_filename(__name__, path))

def checkParam(v: str, list, dv: str):
    if isEmptyString(v):
        return dv
    return v if (v in list) else dv

def checkIntParam(v: str, dv: int):
    if isEmptyString(v):
        return dv
    try:
        return int(v, 10)
    except:
        return dv

def loadConfig(config:str):
    yamlPath = resourcePath("./config/" + config + ".yaml")
    with open(yamlPath, encoding='utf-8') as file1:
        data = yaml.load(file1,Loader=yaml.FullLoader)#读取yaml文件
        # salf_load_all方法得到的是一个迭代器，需要使用list()方法转换为列表
        print(data)
        return (data)

def setupOss():
    config = loadConfig("oss")
    # 阿里云账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM用户进行API访问或日常运维，请登录RAM控制台创建RAM用户。
    auth = oss2.Auth(config.get('access_key_id'), config.get('access_key_secret'))
    # 填写自定义域名，例如example.com。
    cname = config.get('cname')
    bucketName = config.get('bucket')
    # 填写Bucket名称，并设置is_cname=True来开启CNAME。CNAME是指将自定义域名绑定到存储空间。
    bucket = oss2.Bucket(auth, cname, bucketName, is_cname=config.get('useCName'))
    return bucket


def uploadToOss(localFile):
    # 上传文件到OSS。
    bucket = setupOss()
    print("上传图片到OSS")
    ossKey = (
        "ad/"
        + (datetime.datetime.now().strftime("%Y/%m%d/%H"))
        + "/"
        + (localFile.split(os.sep).pop())
    )
    bucket.put_object_from_file(ossKey, localFile)
    return "https://i.wuqiwen.cn/" + ossKey


def getTempFileName(extName):
    # 生成一个随机字符串
    uuid_str = uuid.uuid4().hex
    # 构成完整文件存储路径
    tmp_file_name = "tmpfile_%s.%s" % (uuid_str, extName)
    return tmp_file_name
    # return os.path.join(tempfile.gettempdirb(),tmp_file_name)


def downloadFile(url, outfile):
    data = requests.get(url, allow_redirects=True)
    open(outfile, "wb").write(data.content)


def isNotEmptyString(str: str):
    return type(str) == type("") and len(str) > 0 and str.isspace() == False


def isEmptyString(str: str):
    """
    是否空白字符串（只有空格也算）
    """
    return type(str) == type("") and (len(str) == 0 or str.isspace() == True)


def getExtName(imgUrl: str, dv: str):
    a = imgUrl.split("/")
    b = a.pop().split(".")
    return dv if len(b) == 1 else b[len(b) - 1]


def imageToAnnotations(imgUrl):
    # https://i.wuqiwen.cn/tmp/001.png
    imgFile = os.path.join(
        tempfile.gettempdir(), getTempFileName(getExtName(imgUrl, "jpg"))
    )
    downloadFile(imgUrl, imgFile)
    char_dir = tempfile.mkdtemp("", "char-")
    if os.path.exists(char_dir):
        print(char_dir)
    if os.path.exists(imgFile):
        print(imgFile)
    print("处理图片")
    image_to_annotations(imgFile, char_dir)
    return char_dir


class AnimateDrawingsView(Resource):
    def get(self):
        img = request.args.get("img")
        char = resourcePath("../examples/characters/char1")
        type = checkParam(request.args.get("type"), ["gif", "mp4"], "gif")
        output = checkParam(request.args.get("output"), ["json", "file"], "json")
        
        # 1 处理图片，必须指定`img`参数，如果未指定忽略`img`参数
        # 2 合成动画
        # 3 = 1+2 处理图片再合成动画
        mode = checkIntParam(request.args.get('mode'), 2)
        if (mode & 1) == 1 :
            if isEmptyString(img):
                return {"code": 404, "success": False, "message": "img error"}
            try:
                char = imageToAnnotations(img)
            except Exception as e:
                return {"code": 500, "success": False, "message": e}
        # print(mode)
        if (mode & 2) != 2:
            # 不执行第二步
            if (mode & 1) == 1 :
                return {
                    "code":0,
                    "success": True,
                    "data": char
                }
            else:
                return {'code': 500, "success": True, 'message': 'mode error'}
        
        motion_cfg = checkParam(
            request.args.get("motion"),
            ["dab", "jesse_dance", "jumping", "jumping_jacks", "wave_hello", "zombie"],
            "dab",
        )
        if isEmptyString(motion_cfg):
            return {"code": 404, "success": False, "message": "motion error"}
        else:
            motion_cfg_fn = resourcePath("../examples/config/motion/" + motion_cfg + ".yaml")

        retarget = checkParam(
            request.args.get("retarget"),
            [
                "cmu1_pfp",
                "fair1_ppf",
                "fair1_ppf_duo1",
                "fair1_ppf_duo2",
                "fair1_spf",
                "four_legs",
                "mixamo_fff",
                "six_arms",
            ],
            "fair1_ppf",
        )
        if isEmptyString(retarget):
            return {"code": 404, "success": False, "message": "retarget error"}
        else:
            retarget_cfg_fn = resourcePath("../examples/config/retarget/" + retarget + ".yaml")
        # 输出
        outDir = tempfile.gettempdir()
        outfile = getTempFileName(type)
        annotations_to_animation(
            char, motion_cfg_fn, retarget_cfg_fn, os.path.join(outDir, outfile)
        )
        print(os.path.join(outDir, outfile))
        ossImgUrl = uploadToOss(os.path.join(outDir, outfile))
        if output == "json":
            return {"code": 0, "success": True, "data": ossImgUrl}
        else:
            return send_from_directory(outDir, outfile)

    def post(self):
        return {"code": 200}
