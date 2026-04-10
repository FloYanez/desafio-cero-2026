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
  - backoffice.html
- static/
  - style.css

## Instalar requerimientos
``` bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Correr app
```bash
venv\Scripts\activate
python app.py
```
Ir a [http://localhost:5000](http://localhost:5000)

## Decisiones de diseño
- **Server-side rendering con Jinja2**: el frontend es HTML puro con formularios, sin JavaScript. Dado el alcance del proyecto no justificaba la complejidad de un framework frontend separado.
- **Guard de doble booking**: antes de guardar, re-verifica disponibilidad para evitar que dos usuarios agenden el mismo bloque simultáneamente.
- **Sin restricción de fecha mínima**: el enunciado dice explícitamente que se pueden tomar horas para fechas pasadas.
- **Paciente hardcodeado**: se usa un RUT fijo para identificar al paciente. Una implementación real requeriría autenticación, pero no era parte del alcance del ejercicio.
- **Backoffice sin autenticación**: el enlace al backoffice en la barra de navegación y la falta de login son solo para propósito de este ejercicio. Una implementación real requeriría autenticación.
- **Haber usado React** para el frontend habría permitido testear el backend como API REST pura, pero dada la escala del proyecto es más sencillo usar Jinja2.
