from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime, timedelta, time as time_t, date as date_t

app = Flask(__name__)
app.secret_key = "clave-secreta-dev"

@app.template_filter("format_date")
def format_date(iso_str):
    d = date_t.fromisoformat(iso_str)
    months = ["enero","febrero","marzo","abril","mayo","junio",
              "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    days = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    return f"{days[d.weekday()]} {d.day} de {months[d.month - 1]} de {d.year}"

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


@app.route("/", methods=["GET", "POST"])
def index():
    today = date_t.today().isoformat()

    if request.method == "POST":
        date_str = request.form.get("date", "")
        time_str = request.form.get("time", "")
        appt_type = request.form.get("type", "").upper()

        try:
            target_date = date_t.fromisoformat(date_str)
            start_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            flash("Fecha u hora inválida.", "error")
            return redirect(url_for("index", date=date_str, type=appt_type))

        start_dt = datetime.combine(target_date, start_time)
        end_dt = start_dt + timedelta(minutes=DURATIONS[appt_type])

        available = get_available_slots(target_date, appt_type)
        if time_str not in [s["start"] for s in available]:
            flash("Ese bloque ya no está disponible.", "error")
            return redirect(url_for("index", date=date_str, type=appt_type))

        appointments = load_appointments()
        appointments.append({
            "start": start_dt,
            "end": end_dt,
            "type": appt_type,
            "patient_id": PATIENT_ID,
        })
        save_appointments(appointments)

        flash(f"¡Cita agendada para el {target_date.strftime('%d/%m/%Y')} a las {time_str}!", "success")
        return redirect(url_for("index", date=date_str, type=appt_type))

    # GET
    date_str = request.args.get("date", today)
    appt_type = request.args.get("type", "EVALUACION").upper()

    try:
        target_date = date_t.fromisoformat(date_str)
    except ValueError:
        target_date = date_t.today()
        date_str = today

    if appt_type not in ("EVALUACION", "TRATAMIENTO"):
        appt_type = "EVALUACION"

    # Solo calcular slots si el usuario envió el formulario explícitamente
    submitted = "date" in request.args
    slots = get_available_slots(target_date, appt_type) if submitted else None

    return render_template(
        "index.html",
        patient_id=PATIENT_ID,
        today=today,
        date=date_str,
        appt_type=appt_type,
        slots=slots,
    )


if __name__ == "__main__":
    app.run(debug=True)
