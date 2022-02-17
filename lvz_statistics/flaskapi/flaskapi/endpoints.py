from flask import jsonify
from flask import Response
from flask import request
from flask import g
import datetime
import json
from flaskapi import app
import pydevd_pycharm
from elasticsearch import Elasticsearch


@app.route('/api/test', methods=['GET'])
def test():
    es_client = Elasticsearch('http://elasticsearch:9200')
    data = es_client.search(index='lvz_articles', body={
        "query": {
            "bool": {
                "must_not": {
                    "match_phrase": {
                        "doc.organization": "lvz"
                    }
                }
            }
        },
        "size": 0,
        "aggs": {
            "article_count_over_time": {
                "date_histogram": {
                    "field": "doc.published_at",
                    "calendar_interval": "month",
                    "extended_bounds": {
                        "min": "2020-01-01T00:00:00",
                        "max": "2021-12-01T00:00:00"
                    },
                    "min_doc_count": 0
                }
            }
        }
    })
    return data['aggregations']['article_count_over_time']