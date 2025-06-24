from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)

# Conexión a MongoDB
client = MongoClient("mongodb+srv://admin:admin123@cluster0.2owahcw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["smart_parking"]
stats = db["estadisticas"]

@app.route("/api/estadisticas/update", methods=["POST"])
def update():
    data = request.get_json()

    tipo = data["tipo_vehiculo"]
    lugar = str(data["estacionamiento_id"])

    # Obtener documento principal
    doc = stats.find_one({"_id": "estadisticas"}) or {
        "_id": "estadisticas",
        "por_tipo_vehiculo": {},
        "por_estacionamiento": {},
        "por_tipo_dia": {},
        "total_registros": 0
    }

    # Actualizar tipo de vehículo
    doc["por_tipo_vehiculo"][tipo] = doc["por_tipo_vehiculo"].get(tipo, 0) + 1

    # Actualizar por estacionamiento
    doc["por_estacionamiento"][lugar] = doc["por_estacionamiento"].get(lugar, 0) + 1

    # Detectar tipo de día (laboral o fin de semana)
    tz = pytz.timezone("America/Argentina/Buenos_Aires")
    hoy = datetime.now(tz).weekday()  # 0 = lunes, 6 = domingo
    tipo_dia = "Laboral" if hoy < 5 else "Fin de Semana"

    doc.setdefault("por_tipo_dia", {})
    doc["por_tipo_dia"][tipo_dia] = doc["por_tipo_dia"].get(tipo_dia, 0) + 1

    # Incrementar registros
    doc["total_registros"] += 1

    # Guardar en MongoDB
    stats.replace_one({"_id": "estadisticas"}, doc, upsert=True)

    return jsonify({"message": "Actualizado"})

@app.route("/api/estadisticas", methods=["GET"])
def obtener():
    data = stats.find_one({"_id": "estadisticas"}, {"_id": 0})
    return jsonify(data or {})

if __name__ == "__main__":
    app.run()
