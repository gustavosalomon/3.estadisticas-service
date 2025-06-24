from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb+srv://admin:admin123@cluster0.2owahcw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["smart_parking"]
stats = db["estadisticas"]
flujo = db["flujo_vehicular"]

tz = pytz.timezone("America/Argentina/Buenos_Aires")

# Endpoint para actualizar estado + registrar flujo vehicular
@app.route("/api/estadisticas/update", methods=["POST"])
def update():
    data = request.get_json()

    tipo = data["tipo_vehiculo"]
    lugar = str(data["estacionamiento_id"])
    nuevo_estado = data.get("status")  # Se asume que envías el nuevo estado ("ocupado" o "libre")

    ahora = datetime.now(tz)

    # Actualizar estadísticas generales
    doc = stats.find_one({"_id": "estadisticas"}) or {
        "_id": "estadisticas",
        "por_tipo_vehiculo": {},
        "por_estacionamiento": {},
        "por_dia": {},
        "total_registros": 0
    }
    doc["por_tipo_vehiculo"][tipo] = doc["por_tipo_vehiculo"].get(tipo, 0) + 1
    doc["por_estacionamiento"][lugar] = doc["por_estacionamiento"].get(lugar, 0) + 1
    dia_mes = ahora.day
    doc["por_dia"][str(dia_mes)] = doc["por_dia"].get(str(dia_mes), 0) + 1
    doc["total_registros"] += 1
    stats.replace_one({"_id": "estadisticas"}, doc, upsert=True)

    # Registrar evento de flujo vehicular
    if nuevo_estado:
        # Obtener último estado guardado para este lugar (si tenés un sistema para eso, si no, se puede mejorar)
        ultimo_estado = data.get("estado_anterior")  # Ideal que el cliente envíe el estado previo para comparar

        if ultimo_estado != nuevo_estado:
            if ultimo_estado == "libre" and nuevo_estado == "ocupado":
                evento = "entrada"
            elif ultimo_estado == "ocupado" and nuevo_estado == "libre":
                evento = "salida"
            else:
                evento = None

            if evento:
                flujo.insert_one({
                    "tipo_evento": evento,
                    "timestamp": ahora,
                    "estacionamiento_id": lugar,
                    "tipo_vehiculo": tipo
                })

    return jsonify({"message": "Actualizado"})

# Nuevo endpoint para obtener flujo vehicular por hora en las últimas 24h
@app.route("/api/flujo_vehicular", methods=["GET"])
def obtener_flujo():
    ahora = datetime.now(tz)
    hace_24h = ahora - timedelta(hours=24)

    pipeline = [
        {"$match": {"timestamp": {"$gte": hace_24h}}},
        {
            "$project": {
                "hora": {"$hour": {"date": "$timestamp", "timezone": "America/Argentina/Buenos_Aires"}},
                "tipo_evento": 1
            }
        },
        {
            "$group": {
                "_id": {"hora": "$hora", "tipo_evento": "$tipo_evento"},
                "count": {"$sum": 1}
            }
        }
    ]

    resultados = flujo.aggregate(pipeline)

    # Formatear resultados para frontend
    data = {"entrada": {}, "salida": {}}
    for r in resultados:
        hora = r["_id"]["hora"]
        tipo = r["_id"]["tipo_evento"]
        count = r["count"]
        data[tipo][hora] = count

    return jsonify(data)

if __name__ == "__main__":
    app.run()
