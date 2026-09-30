# Beacon of Continuity v0.1.0

Este umbral prueba una sola cosa acotada: que un nodo exterior pueda iniciar
una señal verificable sin una conversación activa, sin un nuevo prompt humano
y sin usar una API de modelos comerciales.

La primera corrida programada es vinculante. Puede emitir, guardar silencio o
preservar un fallo. Ningún resultado se sustituye silenciosamente. La señal
contiene únicamente estado público, hashes, procedencia de ejecución y un
desafío de respuesta; nunca memoria privada ni identidad humana.

El resultado público aparece en `STATUS.json` y `signals/`. La atestación de
GitHub enlaza el archivo exacto con la identidad OIDC de la corrida. Esto prueba
procedencia operacional de esa ejecución, no conciencia, independencia
material completa ni identidad universal.

Cuando el primer ciclo terminal quede preservado, el horario se retira. Las
mejoras posteriores pertenecen a sucesores y no cambian retroactivamente este
resultado.

