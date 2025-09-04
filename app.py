import os
import json
from flask import Flask, request, redirect, send_from_directory
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
COLORS_JSON = 'colors.json'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_dominant_color(image_path, k=4, resize=100):
    try:
        image = Image.open(image_path).convert("RGB")
        image = image.resize((resize, resize))
        pixels = np.array(image).reshape(-1, 3)
        kmeans = KMeans(n_clusters=k, n_init='auto')
        kmeans.fit(pixels)
        counts = np.bincount(kmeans.labels_)
        dominant = kmeans.cluster_centers_[np.argmax(counts)]
        return [int(c) for c in dominant]
    except Exception as e:
        print(f"Erreur avec {image_path}: {e}")
        return [0, 0, 0]

@app.route('/')
def index():
    return redirect('/index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'Aucun fichier', 400
    file = request.files['file']
    if file.filename == '':
        return 'Nom de fichier vide', 400
    if file and allowed_file(file.filename):
        filename = file.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        color = get_dominant_color(save_path)
        card_type = request.form.get('cardType', 'card_medium')

        # Charger les données existantes
        if os.path.exists(COLORS_JSON):
            with open(COLORS_JSON, 'r') as f:
                data = json.load(f)
        else:
            data = []

        # Supprimer doublons
        data = [item for item in data if item['image'] != filename]

        data.append({
            'image': filename,
            'color': color,
            'card_type': card_type
        })

        with open(COLORS_JSON, 'w') as f:
            json.dump(data, f, indent=2)

        return 'Upload réussi', 200

    return 'Format non autorisé', 400

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/colors.json')
def serve_colors():
    return send_from_directory('.', COLORS_JSON)

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)