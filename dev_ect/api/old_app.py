from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/hello', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello World from the Flask Container!"})

if __name__ == '__main__':
    # host='0.0.0.0' is required for Docker so it accepts connections from outside the container
    app.run(host='0.0.0.0', port=5000)



