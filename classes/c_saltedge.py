import base64
import os
import time

import Crypto.Hash.SHA as SHA
import Crypto.PublicKey.RSA as RSA
import Crypto.Signature.PKCS1_v1_5 as PKCS1_v1_5
import logging
import requests

_logger = logging.getLogger(__name__)


class SaltEdge:
    def __init__(self, client_id, service_secret):
        os.path.join(os.path.dirname(__file__), 'my_file')
        self.client_id = client_id
        self.service_secret = service_secret
        # self.private_path = 'C:/dev/fundament.it/_keys/private.pem'
        self.private_path = os.path.join(os.path.dirname(__file__), '../static/src/cert/private.pem')
        _logger.info('SaltEdge Cert Private Path: ' + self.private_path)
        # self.public_path = 'C:/dev/fundament.it/_keys/public.pub'
        self.public_path = os.path.join(os.path.dirname(__file__), '../static/src/cert/public.pub')
        _logger.info('SaltEdge Cert Public Path: ' + self.public_path)

        self.private_key = RSA.importKey(open(self.private_path, 'r').read())
        self.public_key = RSA.importKey(open(self.public_path, 'r').read())

    @staticmethod
    def expires_at():
        return int(time.time() + 60)

    def sign(self, string):
        signer = PKCS1_v1_5.new(self.private_key)
        string = SHA.new(string)
        return base64.b64encode(signer.sign(string))

    def verify(self, string, signature):
        verifier = PKCS1_v1_5.new(self.public_key)
        return verifier.verify(SHA.new(string), base64.b64decode(signature))

    def generate_signature(self, method, expire, some_url, payload=""):
        string = "{expire}|{method}|{some_url}|{payload}".format(**locals())
        return self.sign(string)

    def get(self, some_url):
        expire = self.expires_at()
        headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json',
            'Signature': self.generate_signature("GET", expire, some_url),
            'Expires-at': str(expire),
            'Client-id': self.client_id,
            'Service-secret': self.service_secret
        }
        return requests.get(some_url, headers=headers)

    def post(self, some_url, payload):
        expire = self.expires_at()
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'Signature': self.generate_signature("POST", expire, some_url, payload),
            'Expires-at': str(expire),
            'Client-id': self.client_id,
            'Service-secret': self.service_secret
        }
        return requests.post(some_url, data=payload, headers=headers)

    def put(self, some_url, payload):
        expire = self.expires_at()
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'Signature': self.generate_signature("PUT", expire, some_url, payload),
            'Expires-at': str(expire),
            'Client-id': self.client_id,
            'Service-secret': self.service_secret
        }
        return requests.put(some_url, data=payload, headers=headers)

    def delete(self, some_url):
        expire = self.expires_at()
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'Signature': self.generate_signature("DELETE", expire, some_url),
            'Expires-at': str(expire),
            'Client-id': self.client_id,
            'Service-secret': self.service_secret
        }
        return requests.delete(some_url, headers=headers)
