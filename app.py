from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb+srv://admin:admin123@cluster0.2owahcw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["smart_parking"]
stats = db["estadisticas"]

@app.route("/api/estadisticas/update", methods=["POST"])
def update():
    data = request.get_json()
    doc = stats.find_one({"_id": "estadisticas"}) or {
        "_id": "estadisticas",
        "por_tipo_vehiculo": {},
        "por_estacionamiento": {},
        "por_tipo_dia": {},
        "total_registros": 0
    }

    tipo = data["tipo_vehiculo"]
    lugar = str(data["estacionamiento_id"])

    # Obtener fecha de start_time si viene, sino ahora
    fecha = datetime.utcnow()
    if "start_time" in data and data["start_time"]:
        try:
            fecha = datetime.fromisoformat(data["start_time"])
        except Exception:
            pass

    dia_semana = fecha.weekday()  # 0=lunes ... 6=domingo
    if dia_semana < 5:
        tipo_dia = "Laboral"
    else:
        tipo_dia = "Fin de semana"

    doc["por_tipo_vehiculo"][tipo] = doc["por_tipo_vehiculo"].get(tipo, 0) + 1
    doc["por_estacionamiento"][lugar] = doc["por_estacionamiento"].get(lugar, 0) + 1
    doc["por_tipo_dia"][tipo_dia] = doc["por_tipo_dia"].get(tipo_dia, 0) + 1
    doc["total_registros"] += 1

    stats.replace_one({"_id": "estadisticas"}, doc, upsert=True)
    return jsonify({"message": "Actualizado"})

@app.route("/api/estadisticas", methods=["GET"])
def obtener():
    data = stats.find_one({"_id": "estadisticas"}, {"_id": 0})
    return jsonify(data or {})

if __name__ == "__main__":
    app.run()
