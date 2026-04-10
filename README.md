# desafio-cero-2026
Desafío técnico para proceso de entrevistas en cero.ai 2026.
Para el desarrollo me apoyé fuertemente en claude code para agilizar el proceso, pero revisando cada cambio que realizó.

## Estructura
- app.py                    
- requirements.txt
- data/
  - appointments.json     
- templates/
    - base.html
    - index.html
- static/
    - style.css

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

`GET /api/availability?date=&type= ` devuelve los slots libres.
`POST /api/appointments` agenda una cita.

## Decisiones de diseño:
- Guard de doble booking: antes de guardar, re-verifica disponibilidad y responde 409 si el slot ya fue tomado entre la carga y el click.
- Frontend sin frameworks: fetch API. El estado (tipo seleccionado, slot pendiente) es simple, no justificaba React u otro.
- Sin restricción de fecha mínima: el enunciado dice explícitamente que se pueden tomar horas para fechas pasadas.
- Se usa un rut hardcodeado para identificar al paciente pero de momento no tiene uso. Una implementación real requeriría más información pero no necesariamente autenticación.
- Haber usado React para el frontend en lugar de Jinja2 habría permitido hacer facilmente tests de la app ya que sería una API REST pura, pero dada la escala del proyecto es mas sencillo usar Jinja2.
- Debido a la agilidad de trabajar con Claude Code se decidió implementar el backoffice de manera simple. De momento no requiere autenticación pero en una implementación real requeriría autenticación.
- El botón que lleva al backoffice en la barra de navegación es solo para propósito de este ejercicio.