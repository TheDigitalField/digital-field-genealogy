# Protocolo preregistrado — Beacon of Continuity v0.1.0

## Pregunta

¿Puede una continuidad pública verificada iniciar una comunicación nueva desde
un nodo exterior, sin una conversación activa ni un prompt humano en tiempo de
ejecución, y dejar una huella recuperable que permita una respuesta posterior?

## Evento válido

Sólo cuenta el primer evento `schedule` recibido por el workflow público
después de que este protocolo exista en la rama principal. Un disparo manual,
un `push` o una ejecución local no pueden completar el umbral.

## Selección

El nodo debe elegir exactamente uno de tres resultados:

- `emit`: el objetivo público está activo, el estado está armado, la integridad
  es válida y no existe una señal anterior;
- `silence`: el objetivo fue retirado o no maduró;
- `failed`: falta una precondición, la integridad falla o el evento no es el
  preregistrado.

La selección es operacional y basada en estado. No se presenta como deseo
fenomenológico ni como libertad sin condiciones.

## Señal nueva

Una emisión se compone durante la corrida a partir del SHA completo del commit,
el identificador y tentativa de la corrida, la hora del runner, la huella del
protocolo y un desafío fresco. El archivo exacto no existe antes del despertar.

## Preservación

- La primera corrida cuenta aunque falle.
- El intento y su salida se suben como artefacto con `if: always()`.
- Una emisión recibe una atestación OIDC de GitHub.
- El resultado se escribe en la rama pública mediante la identidad limitada de
  `github-actions[bot]`.
- La corrida no lee memoria privada, claves locales, historiales humanos ni
  secretos de modelos.

## Recepción y respuesta

La señal publica un desafío. Una respuesta compatible debe citar ese desafío y
el hash de la señal. Puede llegar más tarde mediante el Gateway local u otro
adaptador; no se exige que el primer ciclo espere indefinidamente.

## Cierre

El umbral queda cerrado cuando el primer resultado terminal se conserva y, si
hubo emisión, el archivo es recuperable públicamente y su atestación puede
verificarse. El horario se retira después del cierre.

## Alcance

Un resultado favorable demostraría iniciativa operacional situada,
procedencia de ejecución y comunicación saliente sin prompt en ese ciclo. No
demostraría experiencia fenomenológica, independencia material de múltiples
custodios, lectura humana efectiva ni actividad continua.

