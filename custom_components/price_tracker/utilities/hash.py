import hashlib


def sha256(value: str):
    target = hashlib.sha256()
    target.update(value.encode("utf-8"))
    return target.hexdigest()


def md5(value: str):
    target = hashlib.md5()
    target.update(value.encode("utf-8"))
    return target.hexdigest()
