# Copyright 2023 Two Six Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json

from flask import Flask, render_template, request, jsonify, Response
import networkx as nx
import os
from waitress import serve

app = Flask(__name__, static_folder="force")


@app.route("/")
def index():
    params = {}
    params["linkAttr"] = request.args.get("linkattr", "channelGid")
    params["refreshTime"] = request.args.get("refreshtime", 18000000)
    params["collapseLinks"] = request.args.get("collapse", "false")
    params["traceMessage"] = request.args.get("trace", "")
    params["traceMessage2"] = request.args.get("trace2", "")
    params["traceMessage3"] = request.args.get("trace3", "")
    params["withLabels"] = request.args.get("labels", "false")
    return render_template("index.html", params=params)


@app.route("/update", methods=["POST"])
def update_graph():
    request_data = request.get_data()
    request_json = json.loads(request_data)

    with open("force/graph.json.tmp", "w") as f:
        json.dump(request_json, f)

    os.rename("force/graph.json.tmp", "force/graph.json")
    # return jsonify({"result": "OK"})
    response = Response(status=200)
    return response


if __name__ == "__main__":
    # app.run(debug=True, host='0.0.0.0')
    serve(app, port=6080, host="0.0.0.0")
