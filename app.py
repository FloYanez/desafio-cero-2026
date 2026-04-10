from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime, timedelta, time as time_t, date as date_t

app = Flask(__name__)

PATIENT_ID = "12345678-9"

DURATIONS = {
    "EVALUACION": 30,
    "TRATAMIENTO": 45,
    "URGENCIA": 90,
}

CLINIC_START = time_t(9, 0)
CLINIC_END = time_t(18, 0)
LUNCH_START = time_t(13, 15)
LUNCH_END = time_t(14, 30)
SLOT_INTERVAL = 15  # minutes

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "appointments.json")


def load_appointments():
    with open(DATA_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    result = []
    for appt in raw:
        # fromisoformat handles -03:00 offset; replace strips tz to treat as local time
        start = datetime.fromisoformat(appt["start"]).replace(tzinfo=None)
        end = datetime.fromisoformat(appt["end"]).replace(tzinfo=None)
        result.append({
            "start": start,
            "end": end,
            "type": appt["type"],
            "patient_id": appt.get("patient_id"),
        })
    return result


def save_appointments(appointments):
    data = []
    for appt in appointments:
        entry = {
            "start": appt["start"].strftime("%Y-%m-%dT%H:%M:%S") + "-03:00",
            "end": appt["end"].strftime("%Y-%m-%dT%H:%M:%S") + "-03:00",
            "type": appt["type"],
        }
        if appt.get("patient_id"):
            entry["patient_id"] = appt["patient_id"]
        data.append(entry)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_available_slots(target_date, appt_type):
    duration = timedelta(minutes=DURATIONS[appt_type])
    appointments = load_appointments()

    day_appointments = [
        a for a in appointments
        if a["start"].date() == target_date
    ]

    clinic_end_dt = datetime.combine(target_date, CLINIC_END)
    lunch_start_dt = datetime.combine(target_date, LUNCH_START)
    lunch_end_dt = datetime.combine(target_date, LUNCH_END)

    slots = []
    current = datetime.combine(target_date, CLINIC_START)

    while current < clinic_end_dt:
        slot_end = current + duration

        if slot_end > clinic_end_dt:
            break

        overlaps_lunch = current < lunch_end_dt and slot_end > lunch_start_dt
        overlaps_appt = any(
            current < a["end"] and slot_end > a["start"]
            for a in day_appointments
        )

        if not overlaps_lunch and not overlaps_appt:
            slots.append({
                "start": current.strftime("%H:%M"),
                "end": slot_end.strftime("%H:%M"),
            })

        current += timedelta(minutes=SLOT_INTERVAL)

    return slots


@app.route("/")
def index():
    today = date_t.today().isoformat()
    return render_template("index.html", patient_id=PATIENT_ID, today=today)


@app.route("/api/availability")
def availability():
    date_str = request.args.get("date", "")
    appt_type = request.args.get("type", "").upper()

    if not date_str or not appt_type:
        return jsonify({"error": "Parámetros faltantes"}), 400
    if appt_type not in ("EVALUACION", "TRATAMIENTO"):
        return jsonify({"error": "Tipo inválido"}), 400

    try:
        target_date = date_t.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "Fecha inválida"}), 400

    slots = get_available_slots(target_date, appt_type)
    return jsonify(slots)


@app.route("/api/appointments", methods=["POST"])
def book_appointment():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "JSON inválido"}), 400

    date_str = body.get("date", "")
    time_str = body.get("time", "")
    appt_type = body.get("type", "").upper()

    if not all([date_str, time_str, appt_type]):
        return jsonify({"error": "Parámetros faltantes"}), 400
    if appt_type not in ("EVALUACION", "TRATAMIENTO"):
        return jsonify({"error": "Tipo inválido"}), 400

    try:
        target_date = date_t.fromisoformat(date_str)
        start_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return jsonify({"error": "Fecha u hora inválida"}), 400

    start_dt = datetime.combine(target_date, start_time)
    end_dt = start_dt + timedelta(minutes=DURATIONS[appt_type])

    # Verify the slot is still available (guards against race conditions)
    available = get_available_slots(target_date, appt_type)
    if time_str not in [s["start"] for s in available]:
        return jsonify({"error": "El bloque ya no está disponible"}), 409

    appointments = load_appointments()
    appointments.append({
        "start": start_dt,
        "end": end_dt,
        "type": appt_type,
        "patient_id": PATIENT_ID,
    })
    save_appointments(appointments)

    return jsonify({
        "success": True,
        "message": "¡Cita agendada exitosamente!",
        "appointment": {
            "date": target_date.strftime("%d/%m/%Y"),
            "start": time_str,
            "end": end_dt.strftime("%H:%M"),
            "type": appt_type,
        },
    }), 201


if __name__ == "__main__":
    app.run(debug=True)
