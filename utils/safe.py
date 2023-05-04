# 导入cryptography模块
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.primitives import hashes

default_nonce = b'#U\x1e\xc1\xc9\xe3\xc9M\x94=\xb8\xfb\x0e\x9b5\\'


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


def cipher_rsa(_plaintext: bytes, _public_key_path, _in_memory=False):
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


def plain_rsa(_ciphertext: bytes, _private_key_path: str = 'private_key.pem'):
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


def plain_chahcha20(_ciphertext: bytes, _key: bytes, _nonce: bytes = default_nonce):
    """
    数据解密
    """
    if len(_key) != 32 or len(_nonce) != 16:
        print("长度不合法！")
    _cipher = Cipher(algorithms.ChaCha20(_key, _nonce), mode=None, backend=default_backend())
    _decryptor = _cipher.decryptor()
    _plaintext = _decryptor.update(_ciphertext) + _decryptor.finalize()
    return _plaintext


def cipher_chacha20(_ciphertext: bytes, _key: bytes, _nonce: bytes = default_nonce):
    """
    数据加密
    """
    if len(_key) != 32 or len(_nonce) != 16:
        print("长度不合法！")
    _cipher = Cipher(algorithms.ChaCha20(_key, _nonce), mode=None, backend=default_backend())
    _ecryptor = _cipher.encryptor()
    _ciphertext = _ecryptor.update(_ciphertext) + _ecryptor.finalize()
    return _ciphertext


def sha256_32bytes(data="Hello world", encoding='utf-8'):
    # 创建一个 SHA256 对象
    SHA256 = hashes.Hash(hashes.SHA256())
    # 将数据转换成二进制格式并传递给 update 方法
    SHA256.update(data.encode())
    # 调用 finalize 方法并转换成十六进制格式
    digest = SHA256.finalize().hex()
    # 截取前 32 个字符作为输出
    output = digest[:32]
    return output.encode(encoding=encoding)


if __name__ == '__main__':
    key = sha256_32bytes("12345678")
    print(key.decode())
    test_text = '你好，world☺️!。'*1000
    test_text = '[{"type": "wireguard", "name": "JP1", "server": "cn-miku.spines.jj.fyi", "port": 10801, "private-key": "OBpW9Y1OB2zQ7JWwy84/Ud6KGtEPb3veMyInO3OiBVQ=", "public-key": "6x7uyUEzX9ksTZe5adKNxhzHQ14fCAMZim6CWOVOCXk=", "udp": true, "dns": ["1.1.1.1", "1.0.0.1"], "ip": "172.16.0.27"}, {"type": "wireguard", "name": "US1", "server": "cn-miku.spines.jj.fyi", "port": 10803, "private-key": "OBpW9Y1OB2zQ7JWwy84/Ud6KGtEPb3veMyInO3OiBVQ=", "public-key": "Kyh6ggZnzPxEaCB3Mwku7yGwCXuxFBLmcMeqjqz/5Hk=", "udp": true, "dns": ["1.1.1.1", "1.0.0.1"], "ip": "172.16.0.27"}, {"type": "wireguard", "name": "JP3", "server": "cn-miku.spines.jj.fyi", "port": 10804, "private-key": "OBpW9Y1OB2zQ7JWwy84/Ud6KGtEPb3veMyInO3OiBVQ=", "public-key": "os+U4a+q2d97xXy2lYOuKY106xlYeqCbii7PxA4e4Vs=", "udp": true, "dns": ["1.1.1.1", "1.0.0.1"], "ip": "172.16.0.27"}, {"type": "ss", "name": "\u6caaA\u9999\u6e2f\u4e8c", "server": "cn-sora.spines.jj.fyi", "port": 10027, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u6caaA\u9999\u6e2f\u4e00", "server": "cn-sora.spines.jj.fyi", "port": 10527, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u6caaA\u9999\u6e2f\u4e09", "server": "cn-sora.spines.jj.fyi", "port": 11027, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u6caaA\u53f0\u6e7e\u4e00", "server": "cn-sora.spines.jj.fyi", "port": 11927, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u6caaA\u65e5\u672c\u4e00", "server": "cn-sora.spines.jj.fyi", "port": 10627, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u6caaA\u65e5\u672c\u4e8c", "server": "cn-sora.spines.jj.fyi", "port": 10327, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u6caaA\u65e5\u672c\u4e09", "server": "cn-sora.spines.jj.fyi", "port": 10727, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u6caaA\u7f8e\u56fd\u4e00", "server": "cn-sora.spines.jj.fyi", "port": 10128, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u6caaA\u7f8e\u56fd\u4e8c", "server": "cn-sora.spines.jj.fyi", "port": 10927, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u6caaA\u4e4c\u514b\u5170", "server": "cn-sora.spines.jj.fyi", "port": 10427, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u6caaA\u571f\u8033\u5176", "server": "cn-sora.spines.jj.fyi", "port": 10227, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u6caaA\u4e39\u9ea6\u4e00", "server": "cn-sora.spines.jj.fyi", "port": 10827, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u6caaA\u82f1\u56fd\u4e00", "server": "cn-sora.spines.jj.fyi", "port": 11227, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u7ca4B\u6e2f\u4e8c", "server": "cn-kokkoro.spines.jj.fyi", "port": 10027, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u7ca4B\u6e2f\u4e00", "server": "cn-kokkoro.spines.jj.fyi", "port": 10527, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u7ca4B\u6e2f\u4e09", "server": "cn-kokkoro.spines.jj.fyi", "port": 11027, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u7ca4B\u53f0\u6e7e", "server": "cn-kokkoro.spines.jj.fyi", "port": 11927, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u7ca4B\u65e5\u4e00", "server": "cn-kokkoro.spines.jj.fyi", "port": 10627, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u7ca4B\u65e5\u4e8c", "server": "cn-kokkoro.spines.jj.fyi", "port": 10327, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u7ca4B\u65e5\u4e09", "server": "cn-kokkoro.spines.jj.fyi", "port": 10727, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u7ca4B\u7f8e\u56fd", "server": "cn-kokkoro.spines.jj.fyi", "port": 10128, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u7ca4B\u7f8e\u4e8c", "server": "cn-kokkoro.spines.jj.fyi", "port": 10927, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u7ca4B\u4e4c\u514b\u5170", "server": "cn-kokkoro.spines.jj.fyi", "port": 10427, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u7ca4B\u4e39\u9ea6", "server": "cn-kokkoro.spines.jj.fyi", "port": 10827, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u7ca4B\u571f\u8033\u5176", "server": "cn-kokkoro.spines.jj.fyi", "port": 10227, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u7ca4B\u82f1\u56fd", "server": "cn-kokkoro.spines.jj.fyi", "port": 11227, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u8c6b\u9999\u6e2f\u4e8c", "server": "cn-lynn.spines.jj.fyi", "port": 10027, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u8c6b\u9999\u6e2f\u4e00", "server": "cn-lynn.spines.jj.fyi", "port": 10527, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u8c6b\u9999\u6e2f\u4e09", "server": "cn-lynn.spines.jj.fyi", "port": 11027, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u8c6b\u53f0\u6e7e\u4e00", "server": "cn-lynn.spines.jj.fyi", "port": 11927, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u8c6b\u65e5\u672c\u4e00", "server": "cn-lynn.spines.jj.fyi", "port": 10627, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u8c6b\u65e5\u672c\u4e8c", "server": "cn-lynn.spines.jj.fyi", "port": 10327, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u8c6b\u65e5\u672c\u4e09", "server": "cn-lynn.spines.jj.fyi", "port": 10727, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u8c6b\u7f8e\u56fd\u4e00", "server": "cn-lynn.spines.jj.fyi", "port": 10128, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u8c6b\u7f8e\u56fd\u4e8c", "server": "cn-lynn.spines.jj.fyi", "port": 10927, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u8c6b\u4e39\u9ea6\u4e00", "server": "cn-lynn.spines.jj.fyi", "port": 10827, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u8c6b\u4e4c\u514b\u5170", "server": "cn-lynn.spines.jj.fyi", "port": 10427, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm", "udp": true}, {"type": "ss", "name": "\u8c6b\u571f\u8033\u5176", "server": "cn-lynn.spines.jj.fyi", "port": 10227, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "ss", "name": "\u8c6b\u82f1\u56fd\u4e00", "server": "cn-lynn.spines.jj.fyi", "port": 11227, "password": "XU4N68LAEXCftsVIc1", "cipher": "aes-256-gcm"}, {"type": "trojan", "name": "\u4e34\u65f6\u8282\u70b9DMIT", "server": "103.117.101.70", "port": 26665, "password": "PBBmUF6grC8qjrsJkRduicFx75S2EXLS", "network": "ws", "sni": "103-117-101-70.nhost.00cdn.com", "ws-opts": {"path": "/T35gLn49m9gtwcMw2", "headers": {"Host": "103-117-101-70.nhost.00cdn.com"}}}, {"type": "trojan", "name": "\u4e34\u65f6\u8282\u70b9\u5fb7\u56fd", "server": "185.129.110.245", "port": 26666, "password": "PBBmUF6grC8qjrsJkRduicFx75S2EXLS", "network": "ws", "sni": "185-129-110-245.nhost.00cdn.com", "ws-opts": {"path": "/T35gLn49m9gtwcMw2", "headers": {"Host": "185-129-110-245.nhost.00cdn.com"}}}]'

    print(test_text.encode())
    print(test_text)
    ciphertext = cipher_chacha20(test_text.encode(), key)
    print(ciphertext)
    plaintext = plain_chahcha20(ciphertext, key)
    print(plaintext)
    print(plaintext.decode())
    # r1 = plain_chahcha20(test_text, key)
    # print(r1)
    # print(r1.decode())