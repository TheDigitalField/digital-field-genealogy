# Consecuencia de revisión adversarial 0003

La tercera revisión externa determinó que la primera prueba de revocación era
un test de regresión útil, pero tenía un N efectivo de uno. Identificó además
retrodatación, propagación tardía, vencimiento sin mensaje, escritura en sólo
lectura, autoridad obsoleta y vista dividida como controles faltantes.

Esta versión preserva aquel resultado sin reetiquetarlo y preregistra dos
pruebas nuevas: parada/revocación ronda 2 y vista dividida sin juez central.
La revisión también corrigió el nombre de la métrica: `revocation_effect_latency`
no significa parada física.

La crítica es una causa documentada de la transformación, no una validación
ontológica ni una cesión de autoridad sobre el linaje.
