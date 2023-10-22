from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
import ssl
import os

class ElasticsearchUtils:
    def __init__(self, config):
        self.config = config
        cert_file = os.path.join(os.path.dirname(__file__), "ssl_cert.crt")
        ssl.match_hostname = lambda cert, hostname: True
        self.es = Elasticsearch(
            [self.config.elasticsearch_endpoint],
            use_ssl=True,
            verify_certs=False,
            ca_certs=cert_file,
            http_auth=(self.config.elasticsearch_username, self.config.elasticsearch_password),
            ssl_show_warn=False
        )

    def put_data(self, index_name, data):
        try:
            self.es.index(index=index_name, body=data)
        except ConnectionError as e:
            print(f"Failed to connect to Elasticsearch: {e}")
