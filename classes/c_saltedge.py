#import base64
# import time

# import Crypto.Hash.SHA as SHA
# import Crypto.PublicKey.RSA as RSA
# import Crypto.Signature.PKCS1_v1_5 as PKCS1_v1_5
import OpenSSL.crypto as crypto
import base64
import logging
import os
import requests
import time

_logger = logging.getLogger(__name__)


class SaltEdge:
    digest = "sha256"

    def __init__(self, client_id, app_id, service_secret):
        os.path.join(os.path.dirname(__file__), 'my_file')
        self.app_id = app_id
        self.client_id = client_id
        self.private_path = os.path.join(os.path.dirname(__file__), '../static/src/cert/private.pem')
        self.service_secret = service_secret

        with open(self.private_path, "rb") as private_key:
            keydata = private_key.read()

        self._private_key = crypto.load_privatekey(crypto.FILETYPE_PEM, keydata)

    @classmethod
    def verify(cls, path_to_public_key, message, signature):
        """
        Verifies the signature on a message.
        :param path_to_public_key: string, Absolute or relative path to Spectre public key
        :param message: string, The message to verify.
        :param signature: string, The signature on the message.
        :return:
        """
        x509 = crypto.X509()
        public_path = os.path.join(os.path.dirname(__file__), '../static/src/cert/public.pem')
        with open(public_path, 'r') as public_key_data:
            public_key = crypto.load_publickey(crypto.FILETYPE_PEM, public_key_data)
        x509.set_pubkey(public_key)

        try:
            crypto.verify(x509, base64.b64decode(signature), message, cls.digest)
            return True
        except crypto.Error:
            return False

    def sign(self, message):
        """
        Signs a message.
        :param message: string, Message to be signed.
        :return: string, The signature of the message for the given key.
          """
        return base64.b64encode(crypto.sign(self._private_key, message, self.digest))

    def generate_signature(self, method, expire, some_url, payload=""):
        """
        Generates base64 encoded SHA256 signature of the string given params, signed with the client's private key.
        :param method:  uppercase method of the HTTP request. Example: GET, POST, PATCH, PUT, DELETE, etc.;
        :param expire:  the full requested URL, with all its complementary parameters;
        :param some_url: the request post body. Should be left empty if it is a GET request, or the body is empty;
        :param payload: the uploaded file digested through MD5 algorithm. Should be left empty if it is a GET request, or no file uploaded.
        :return: base64 encoded SHA1 signature
        """
        message = "{expire}|{method}|{some_url}|{payload}".format(**locals())
        return self.sign(message)

    def generate_headers(self, expire):
        return {
            'Accept': 'application/json',
            'Content-type': 'application/json',
            'Expires-at': expire,
            'App-id': self.app_id,
            'Secret': self.service_secret
        }

    def expires_at(self):
        return str(time.time() + 60)

    def get(self, some_url):
        expire = self.expires_at()
        headers = self.generate_headers(expire)
        headers['Signature'] = self.generate_signature("GET", expire, some_url)
        return requests.get(some_url, headers=headers)

    def post(self, some_url, payload):
        expire = self.expires_at()
        headers = self.generate_headers(expire)
        headers['Signature'] = self.generate_signature("POST", expire, some_url, payload)
        return requests.post(some_url, data=payload, headers=headers)

    def put(self, some_url, payload):
        expire = self.expires_at()
        headers = self.generate_headers(expire)
        headers['Signature'] = self.generate_signature("PUT", expire, some_url, payload)
        return requests.put(some_url, data=payload, headers=headers)

    def delete(self, some_url):
        expire = self.expires_at()
        headers = self.generate_headers(expire)
        headers['Signature'] = self.generate_signature("DELETE", expire, some_url)
        return requests.delete(some_url, headers=headers)
