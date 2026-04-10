# Desafío 2

Una clínica dental necesita una app web como sistema de toma de horas para que los pacientes agenden citas.

La clínica tiene tres tipos de atención:

- Evaluación
- Tratamiento
- Urgencia

Los pacientes no pueden agendar citas de Urgencia, sino que el personal de la clínica asigna esas horas en su backoffice. Por otro lado, le dejamos al paciente decidir si quiere tomar una cita de Evaluación o de Tratamiento.

Construye una pequeña app (front y back) que:

- Muestre visualmente los bloques de horario disponibles según el tipo de atención.
- Permita al usuario hacer click en un bloque y agendarlo.
- El backend debe permitir obtener la disponibilidad en base a las reglas, y por otra parte, agendar un bloque disponible.

Envíanos un repo de github (si es privado, compártelo con `mquezada`, `Sergio-P` y `cgarrido1024`) con tu código.

Suposiciones:

- Asume que la clínica sólo cuenta con 1 dentista.
- También asume que el paciente ya se encuentra registrado (puedes inventar un identificador o los datos que estimes conveniente).
- Las citas de Evaluación duran 30 minutos, Tratamiento dura 45 minutos, y Urgencia dura 90 minutos.
- La clínica atiende entre 09:00 y 18:00 hrs, y no atiende entre 13:15 y 14:30 hrs.
- Los pacientes pueden agendar citas que comiencen cada 15 minutos (ej: 09:00, 09:15, 09:30...), siempre y cuando la duración total del tratamiento no tope con otra cita o con el horario de almuerzo/cierre.
- Abajo te pasamos un archivo json con la “base de datos” que dice qué horas se encuentran tomadas hasta ese punto. Asume que podemos tomar horas en cupos para los que ya pasó su fecha.
    - Archivo json con las horas tomadas hasta el momento
        
        ```json
        [
          {
            "start": "2026-01-28T09:00:00-03:00",
            "end": "2026-01-28T09:30:00-03:00",
            "type": "EVALUACION"
          },
          {
            "start": "2026-01-28T10:00:00-03:00",
            "end": "2026-01-28T10:45:00-03:00",
            "type": "TRATAMIENTO"
          },
          {
            "start": "2026-01-28T12:30:00-03:00",
            "end": "2026-01-28T13:15:00-03:00",
            "type": "TRATAMIENTO"
          },
          {
            "start": "2026-01-28T15:00:00-03:00",
            "end": "2026-01-28T16:30:00-03:00",
            "type": "URGENCIA"
          },
          {
            "start": "2026-01-28T17:15:00-03:00",
            "end": "2026-01-28T17:45:00-03:00",
            "type": "EVALUACION"
          },
          {
            "start": "2026-01-29T09:00:00-03:00",
            "end": "2026-01-29T10:30:00-03:00",
            "type": "URGENCIA"
          },
          {
            "start": "2026-01-29T10:30:00-03:00",
            "end": "2026-01-29T12:00:00-03:00",
            "type": "URGENCIA"
          },
          {
            "start": "2026-01-29T16:00:00-03:00",
            "end": "2026-01-29T16:45:00-03:00",
            "type": "TRATAMIENTO"
          }
        ]
        ```
        

Debido a la extensión del desafío y a que debes dedicar máximo 3 horas, no esperamos una aplicación “lista para producción”, pero esperamos que sea funcional. Parte de lo que esperamos evaluar son las decisiones que tomes respecto a lo que incluirás en ese prototipo.