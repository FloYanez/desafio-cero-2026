from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime, timedelta, time as time_t, date as date_t

app = Flask(__name__)
# En producción esto debería venir de una variable de entorno (os.environ.get("SECRET_KEY"))
app.secret_key = "clave-secreta-dev"

# Paciente hardcodeado: en una app real vendría de una sesión autenticada
PATIENT_ID = "12345678-9"

# Duración en minutos de cada tipo de cita
DURATIONS = {
    "EVALUACION": 30,
    "TRATAMIENTO": 45,
    "URGENCIA": 90,
}

CLINIC_START = time_t(9, 0)
CLINIC_END = time_t(18, 0)
LUNCH_START = time_t(13, 15)
LUNCH_END = time_t(14, 30)
SLOT_INTERVAL = 15  # minutos entre inicios de slots posibles

# Ruta absoluta al JSON que actúa como base de datos
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "appointments.json")


# Filtro Jinja2 para mostrar fechas en español (ej: "lunes 28 de enero de 2026")
@app.template_filter("format_date")
def format_date(iso_str):
    d = date_t.fromisoformat(iso_str)
    months = ["enero","febrero","marzo","abril","mayo","junio",
              "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    days = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    return f"{days[d.weekday()]} {d.day} de {months[d.month - 1]} de {d.year}"


def load_appointments():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError:
        # El archivo existe pero no es JSON válido (ej: escritura interrumpida).
        # En producción esto debería loggearse y alertar. Retornamos lista vacía
        # para que la app siga funcionando sin mostrar disponibilidad incorrecta.
        print(f"Advertencia: {DATA_FILE} no es JSON válido. Se asume sin citas.")
        return []

    result = []
    for appt in raw:
        try:
            # fromisoformat parsea el offset -03:00; replace(tzinfo=None) lo descarta
            # para trabajar con datetimes ingenuos (naive), tratando todo como hora local de Chile
            start = datetime.fromisoformat(appt["start"]).replace(tzinfo=None)
            end = datetime.fromisoformat(appt["end"]).replace(tzinfo=None)
        except (ValueError, KeyError):
            # Entrada con fecha malformada o campos faltantes: se ignora para no
            # interrumpir el servicio. En producción esto debería loggearse.
            print(f"Advertencia: cita con formato inválido ignorada: {appt}")
            continue

        if end <= start:
            # Intervalo negativo o nulo: la lógica de solapamiento lo ignoraría
            # silenciosamente, produciendo disponibilidad incorrecta.
            print(f"Advertencia: cita con end <= start ignorada: {appt}")
            continue

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

    clinic_start_dt = datetime.combine(target_date, CLINIC_START)
    clinic_end_dt = datetime.combine(target_date, CLINIC_END)
    lunch_start_dt = datetime.combine(target_date, LUNCH_START)
    lunch_end_dt = datetime.combine(target_date, LUNCH_END)

    def is_valid_appointment(a):
        """Descarta citas que caen completamente fuera del horario de atención
        o dentro del horario de almuerzo — no deberían existir pero si están
        en el JSON no deben afectar la disponibilidad."""
        if a["start"].date() != target_date:
            return False
        entirely_outside = a["end"] <= clinic_start_dt or a["start"] >= clinic_end_dt
        entirely_at_lunch = a["start"] >= lunch_start_dt and a["end"] <= lunch_end_dt
        return not entirely_outside and not entirely_at_lunch

    day_appointments = [a for a in appointments if is_valid_appointment(a)]

    slots = []
    current = clinic_start_dt

    while current < clinic_end_dt:
        slot_end = current + duration

        if slot_end > clinic_end_dt:
            break

        # Dos intervalos [A, B) y [C, D) se solapan si A < D y B > C.
        # Un slot que termina exactamente cuando empieza el almuerzo (o una cita) NO solapa.
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

        if appt_type not in ("EVALUACION", "TRATAMIENTO"):
            flash("Tipo de cita inválido.", "error")
            return redirect(url_for("index", date=date_str))

        try:
            target_date = date_t.fromisoformat(date_str)
            start_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            flash("Fecha u hora inválida.", "error")
            return redirect(url_for("index", date=date_str, type=appt_type))

        start_dt = datetime.combine(target_date, start_time)
        end_dt = start_dt + timedelta(minutes=DURATIONS[appt_type])

        # Re-verificar disponibilidad al momento de confirmar para evitar
        # que dos usuarios agenden el mismo bloque simultáneamente
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

    # Solo calcular slots si el usuario envió el formulario; evita mostrar
    # datos en la carga inicial antes de que el paciente elija fecha y tipo
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


@app.route("/backoffice", methods=["GET", "POST"])
def backoffice():
    today = date_t.today().isoformat()

    if request.method == "POST":
        date_str = request.form.get("date", "")
        time_str = request.form.get("time", "")
        patient_id = request.form.get("patient_id", "").strip()

        if not patient_id:
            flash("El RUT del paciente es obligatorio.", "error")
            return redirect(url_for("backoffice", date=date_str, patient_id=patient_id))

        try:
            target_date = date_t.fromisoformat(date_str)
            start_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            flash("Fecha u hora inválida.", "error")
            return redirect(url_for("backoffice", date=date_str, patient_id=patient_id))

        start_dt = datetime.combine(target_date, start_time)
        end_dt = start_dt + timedelta(minutes=DURATIONS["URGENCIA"])

        # Re-verificar disponibilidad al momento de confirmar (mismo motivo que en index)
        available = get_available_slots(target_date, "URGENCIA")
        if time_str not in [s["start"] for s in available]:
            flash("Ese bloque ya no está disponible.", "error")
            return redirect(url_for("backoffice", date=date_str, patient_id=patient_id))

        appointments = load_appointments()
        appointments.append({
            "start": start_dt,
            "end": end_dt,
            "type": "URGENCIA",
            "patient_id": patient_id,
        })
        save_appointments(appointments)

        flash(f"Urgencia agendada para {patient_id} el {target_date.strftime('%d/%m/%Y')} a las {time_str}.", "success")
        return redirect(url_for("backoffice", date=date_str))

    # GET
    date_str = request.args.get("date", today)
    patient_id = request.args.get("patient_id", "")

    try:
        target_date = date_t.fromisoformat(date_str)
    except ValueError:
        target_date = date_t.today()
        date_str = today

    submitted = "date" in request.args
    slots = get_available_slots(target_date, "URGENCIA") if submitted else None

    return render_template(
        "backoffice.html",
        today=today,
        date=date_str,
        patient_id=patient_id,
        slots=slots,
    )


if __name__ == "__main__":
    app.run(debug=True)
