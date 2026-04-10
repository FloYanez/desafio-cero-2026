# desafio-cero-2026
Desafío técnico para proceso de entrevistas en cero.ai 2026.
Para el desarrollo me apoyé fuertemente en claude code para agilizar el proceso, pero revisando cada cambio que realizó.

## Estructura

desafio-cero-2026/
├── app.py                    # Backend Flask
├── requirements.txt
├── data/
│   └── appointments.json     # "base de datos"
├── templates/
│   ├── base.html
│   └── index.html
└── static/
    ├── style.css
    └── app.js

## Instalar requerimientos
``` bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
deactivate
```

## Correr app
```bash
venv\Scripts\activate
python app.py
```
Ir a [http://localhost:5000/?date=2026-01-28&type=EVALUACION](http://localhost:5000/?date=2026-01-28&type=EVALUACION)


## Endpoints

`GET /api/availability?date=&type= ` devuelve los slots libres; 
`POST /api/appointments` agenda una cita.

## Decisiones de diseño:

- Lógica de disponibilidad: itera slots de 15 min dentro del horario clínico, filtrando los que colisionan con almuerzo (13:15–14:30) u otras citas — con bordes estrictos (slot_end > otro_start, no >=), para que un slot que termina justo cuando empieza otro sea válido.
- Guard de doble booking: antes de guardar, re-verifica disponibilidad y responde 409 si el slot ya fue tomado entre la carga y el click.
- Frontend sin frameworks: fetch API + vanilla JS. El estado (tipo seleccionado, slot pendiente) es simple, no justificaba React u otro.
- Sin restricción de fecha mínima: el enunciado dice explícitamente que se pueden tomar horas para fechas pasadas.