from urllib.parse import urlparse
from hashlib import md5
import requests
import tempfile
import os


def isNotEmptyString(str: str):
    """
    非空白字符串（只有空格）返回：`True`
    """
    return type(str) == type("") and len(str) > 0 and str.isspace() == False


def isEmptyString(str: str):
    """
    空白字符串（只有空格也算）返回：`True`，
    `None` 返回：`False`
    """
    return type(str) == type("") and (len(str) == 0 or str.isspace() == True)


def isNullOrEmptyString(str: str):
    """
    空白字符串（只有空格也算）返回：`True`，
    `None` 返回：`True`
    """
    return str == None or isEmptyString(str)


def md5Str(str: str):
    obj = md5()
    obj.update(str.encode("utf-8"))
    bs = obj.hexdigest()
    return bs


def checkUri(url: str):
    """
    判断是否是合法的Uri，必须包含`scheme`、`hostname`、`path`，并且`scheme`是`http`、`https`、`ftp`之一。
    例如：`https://www.xbei.net/i/logo.ico` 返回 `True`；
    `http://www.xbei.net` 返回 `False`
    """
    uri = urlparse(url)
    schemes = ["https", "http", "ftp"]
    return (
        isNotEmptyString(uri.scheme)
        and isNotEmptyString(uri.hostname)
        and isNotEmptyString(uri.path)
        and schemes.index(uri.scheme) >= 0
    )

def getExtName(imgUrl: str, dv: str):
    """
    检查`imgUrl`是否包含后缀名，返回示例：'.jpg'，如果返回`dv`不会加上“.”
    """
    a = imgUrl.split("/")
    b = a.pop().split(".")
    return dv if len(b) == 1 else "." + b[len(b) - 1]

def downloadFile(url:str, outfile:str):
    data = requests.get(url, allow_redirects=True)
    open(outfile, "wb").write(data.content)

def checkAndDownloadFile(url:str, outfile:str):
    """
    检查`outfile`是否存在，存在直接返回否则下载文件后再返回
    """
    if os.path.exists(outfile): return outfile
    data = requests.get(url, allow_redirects=True)
    open(outfile, "wb").write(data.content)
    return outfile

def downloadFileCache(url:str):
    """
    按`url`的字符串Md5判断是否下载过
    """
    code = md5Str(url)
    extName = getExtName(url, '')
    outDir = tempfile.gettempdir()
    outFile = os.path.abspath(os.path.join(outDir, code + extName))
    if os.path.exists(outFile): return outFile
    downloadFile(url, outFile)
    return outFile