from flask import Flask, request, jsonify
from flask_cors import CORS      ## TODO: check if we can add CORS on client side
import pymongo
import configparser
import ssl
from bson import json_util

#Reading current config from file
config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
CORS(app)

def response(caseList):
    return {
        'data': {
            'variables': {
                'result' : caseList
            }
        }
    }

@app.route("/")
def index():
    return "Hello, World!"

@app.route("/ACI")
def index_aci():
    return "Hello, World ACI!"

@app.route('/sydhttsdb', methods=['POST'])
def getHTTS():
    try:
        from mongo_models import HTTSMongo
        cases = HTTSMongo(config).getAHRecords()
        return response(cases)
    except Exception as e:
        return "exception===" + str(e)

if __name__ == '__main__':
    ## TODO. Remove "pip install pyOpenSSL" and use an actual cert.
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_OPTIONAL
    context.load_verify_locations('../ssl/Issuing_CA.cer')
    context.load_cert_chain('../ssl/syd-htts-prd.cisco.com-63411.cer', '../ssl/PrivateKeyForFlask.key')
    app.run(host= '0.0.0.0', port=8443, ssl_context=context, debug=True)
