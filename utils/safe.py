# 导入cryptography模块
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


def gen_key(key_name: str = 'fulltclash', in_memory=False):
    """
    生成配套公私钥
    in_memory: 仅在程序运行时存在
    """
    # 生成一对公钥和私钥（2048位）
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    # 将公钥和私钥序列化为PEM格式，并保存到文件或者返回
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    if in_memory:
        return pem_private, pem_public
    else:
        with open(f'./key/{key_name}-private.pem', 'wb') as f:
            f.write(pem_private)
        with open(f'./key/{key_name}-public.pem', 'wb') as f:
            f.write(pem_public)
        return None, None


def get_key(key_path: str, key_type: str):
    """
    读取公私钥
    key_path: 密钥路径
    key_type: 密钥类型[public, private]
    """
    if key_type == 'private':
        with open(key_path, 'rb') as f:
            pem_private = f.read()
        private_key = serialization.load_pem_private_key(
            pem_private,
            password=None,
            backend=default_backend()
        )
        return private_key
    elif key_type == 'public':
        with open(key_path, 'rb') as f:
            pem_public = f.read()
        public_key = serialization.load_pem_public_key(
            pem_public,
            backend=default_backend()
        )
        return public_key
    else:
        raise TypeError('Unknown key type')


def cipher(_plaintext: bytes, _public_key_path, _in_memory=False):
    """
    数据加密
    _public_key_path: 可以是从本地获取，也可以从内存获取
    """
    public_key = _public_key_path if _in_memory else get_key(_public_key_path, 'public')
    # 使用公钥对文本进行加密，并保存到文件中
    _ciphertext = public_key.encrypt(
        _plaintext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return _ciphertext


def plain(_ciphertext: bytes, _private_key_path: str = 'private_key.pem'):
    """
    数据解密
    """
    private_key = get_key(_private_key_path, 'private')
    _plaintext = private_key.decrypt(
        _ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return _plaintext


if __name__ == '__main__':
    ciphertext = cipher(b'hello word', '../key/fulltclash-public.pem')
    print(ciphertext)
    plaintext = plain(ciphertext, '../key/fulltclash-private.pem')
    print(plaintext)
    print(plaintext.decode(encoding='utf-8'))
