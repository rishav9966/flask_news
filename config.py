import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRTE_KEY') or b'\xac\xaeT\xe7\xf0^\xa6\x10\xe0\xd2\xe7\xccug\xc1\x16'