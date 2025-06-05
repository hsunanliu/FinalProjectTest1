from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/geocode')
def geocode():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Missing query'}), 400

    url = f'https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1'
    headers = {'User-Agent': 'project_dapp'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='localhost', port=5000)
