from flask import Flask
from flask_restful import Api,Resource,request

from animateDrawings import AnimateDrawingsView

app = Flask(__name__)
api = Api(app)


api.add_resource(AnimateDrawingsView,'/api/v1/ad')
if __name__ == '__main__':
    app.run(
        host = '0.0.0.0'
    )