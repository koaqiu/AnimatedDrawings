from flask_restful import Api, Resource, request
from flask import send_from_directory
import yaml
import uuid
import os
import tempfile
from annotations_to_animation import annotations_to_animation
from image_to_annotations import image_to_annotations
from pkg_resources import resource_filename
import utils
from oss import OssClient


def resourcePath(path:str):
    return path if os.path.isabs(path) else os.path.abspath(resource_filename(__name__, path))

def checkParam(v: str, list, dv: str):
    if utils.isEmptyString(v):
        return dv
    return v if (v in list) else dv

def checkIntParam(v: str, dv: int):
    if utils.isEmptyString(v):
        return dv
    try:
        return int(v, 10)
    except:
        return dv

def loadConfig(cgfName:str):
    configPath = os.environ.get('AD_API_CONFIG')
    configPath = configPath if utils.isNotEmptyString(configPath) else "./config"
    yamlPath = resourcePath(configPath + "/" + cgfName + ".yaml")
    with open(yamlPath, encoding='utf-8') as file1:
        data = yaml.load(file1,Loader=yaml.FullLoader)#读取yaml文件
        # salf_load_all方法得到的是一个迭代器，需要使用list()方法转换为列表
        print(type(data))
        return (data)

def getTempFileName(extName):
    # 生成一个随机字符串
    uuid_str = uuid.uuid4().hex
    # 构成完整文件存储路径
    tmp_file_name = "tmpfile_%s.%s" % (uuid_str, extName)
    return tmp_file_name
    # return os.path.join(tempfile.gettempdirb(),tmp_file_name)

def getExtName(imgUrl: str, dv: str):
    a = imgUrl.split("/")
    b = a.pop().split(".")
    return dv if len(b) == 1 else b[len(b) - 1]


def imageToAnnotations(imgUrl):
    # https://i.wuqiwen.cn/tmp/001.png
    imgFile = os.path.join(
        tempfile.gettempdir(), getTempFileName(getExtName(imgUrl, "jpg"))
    )
    utils.checkAndDownloadFile(imgUrl, imgFile)
    char_dir = tempfile.mkdtemp("", "char-")
    if os.path.exists(char_dir):
        print(char_dir)
    if os.path.exists(imgFile):
        print(imgFile)
    print("处理图片")
    config = loadConfig("ad")
    image_to_annotations(imgFile, char_dir, config.get('host'))
    return char_dir

def error(code:int, message:str):
    return {"code": code, "success": False, "message": message}
def success(data):
    return {"code": 0, "success": True, "message": 'success', 'data': data}

class AnimateDrawingsView(Resource):
    def __init__(self) -> None:
        super().__init__()
        self.ossClient = OssClient(loadConfig('oss'))
    def get(self):
        img = request.args.get("img")
        char = resourcePath("../examples/characters/char1")
        type = checkParam(request.args.get("type"), ["gif", "mp4"], "gif")
        output = checkParam(request.args.get("output"), ["json", "file"], "json")
        background = request.args.get('background')
        motion_cfg = checkParam(
            request.args.get("motion"),
            ["dab", "jesse_dance", "jumping", "jumping_jacks", "wave_hello", "zombie"],
            "dab",
        )
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
        # 1 处理图片，必须指定`img`参数，如果未指定忽略`img`参数
        # 2 合成动画
        # 3 = 1+2 处理图片再合成动画
        mode = checkIntParam(request.args.get('mode'), 2)
        
        # 在正式执行相关动作之前先校验一下参数
        if (mode & 2) == 2 :
            if utils.isNotEmptyString(background) :
                if utils.checkUri(background) == False :
                    return error(400, 'background error')
                else:
                    # 下载背景图片
                    background = utils.downloadFileCache(background)
            if utils.isEmptyString(motion_cfg):
                return error(400, "motion error")
            else:
                motion_cfg_fn = resourcePath("../examples/config/motion/" + motion_cfg + ".yaml")

            if utils.isEmptyString(retarget):
                return error(400, "retarget error")
            else:
                retarget_cfg_fn = resourcePath("../examples/config/retarget/" + retarget + ".yaml")

        if (mode & 1) == 1 :
            if utils.isEmptyString(img):
                return error(400, "img error")
            try:
                char = imageToAnnotations(img)
            except Exception as e:
                return error(500, e)
        
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
                return error(400, 'mode error')
        # 输出
        outDir = tempfile.gettempdir()
        outfile = getTempFileName(type)
        annotations_to_animation(
            char, motion_cfg_fn, retarget_cfg_fn, 
            background,
            os.path.join(outDir, outfile)
        )
        print(os.path.join(outDir, outfile))
        if output == "json":
            ossImgUrl = self.ossClient.uploadToOss(os.path.join(outDir, outfile))
            return success(ossImgUrl)
        else:
            return send_from_directory(outDir, outfile)

    def post(self):
        return {"code": 200}
