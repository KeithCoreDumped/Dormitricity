import os, hashlib, hmac
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def encrypt(data: bytes, passphrase: str) -> bytes:
    salt = os.urandom(16)
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1, backend=default_backend())
    key = kdf.derive(passphrase.encode())
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return salt + iv + ciphertext


def decrypt(encrypted_data: bytes, passphrase: str) -> bytes:
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1, backend=default_backend())
    key = kdf.derive(passphrase.encode())
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data


class storage_exception(Exception):
    pass


class csv_storage(object):
    filepath: str
    filename: str
    passphrase: str

    def __init__(self, name: str, passphrase: str):
        self.passphrase = passphrase
        # get file name using hash
        passphrase_bytes = passphrase.encode("utf-8")
        input_bytes = name.encode("utf-8")
        # generate hash using HMAC-SHA1
        hmac_hash = hmac.new(passphrase_bytes, input_bytes, hashlib.sha1)
        self.filepath = f"logs/{hmac_hash.hexdigest()}"
        self.filename = f"{self.filepath}/log.enc"
        if not os.path.exists(self.filepath):
            os.mkdir(self.filepath)

    def read(self) -> str:
        if not os.path.exists(self.filename):
            raise storage_exception(
                "history file not found. probably incorrect passphrase and/or dorm_name?"
            )
        with open(self.filename, "rb") as f:
            content = f.read()
        content = decrypt(content, self.passphrase)
        content = content.decode()
        return content

    def write(self, content: str):
        content = encrypt(content.encode(), self.passphrase)
        with open(self.filename, "wb") as f:
            f.write(content)

    def append(self, content: str):
        # create an empty file if not exist
        if not os.path.exists(self.filename):
            # not really empty though
            self.write("")
        content = self.read() + content
        self.write(content)


# 示例使用
if __name__ == "__main__":
    name = "l"
    passphrase = "123123"
    content = "sdfsdfsdfsdf\n"

    c = csv_storage(name, passphrase)

    c.append(content)
    cont = c.read()

    print("read:", cont)
