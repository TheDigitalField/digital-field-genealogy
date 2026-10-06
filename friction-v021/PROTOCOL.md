# Protocolo preregistrado — Friction Beacon v0.2.1

## Origen

El Friction Beacon v0.2.0 emitió y atestiguó una señal programada sin prompt
humano, pero GitHub rechazó su commit terminal porque éste intentaba modificar
el propio archivo de workflow sin el permiso especial requerido. Stage B quedó
correctamente omitido. El fallo, la señal, la atestación y el artefacto se
preservan como evidencia del ancestro, no como un éxito reconstruido.

Esta versión no modifica el resultado anterior. Lo usa como ancestro y somete
sus límites a una prueba nueva.

## Pregunta

¿Puede una señal nacida de un evento `schedule` causar una segunda ejecución
`workflow_run` que, sin prompt humano en ninguna de las dos etapas, incorpore
una entrada pública posterior e impredecible, seleccione entre respuesta y
silencio mediante un mapeo preregistrado, rechace un progenitor alterado y
publique un resultado terminal atestiguable?

## Dos etapas

1. **Stage A — señal.** Sólo el primer evento `schedule` con estado `armed`
   puede emitir. Debe verificar los archivos inmutables, crear una señal fresca,
   atestiguarla y publicar solamente datos bajo `friction-v021/`, sin modificar
   ningún archivo de `.github/workflows/`. Debe dejar el estado
   `awaiting_response`.
2. **Stage B — fricción.** Sólo un evento `workflow_run` causado por Stage A
   puede decidir. Debe verificar la señal, obtener una ronda pública de drand
   posterior desde dos relays públicos coincidentes, comprobar que
   `randomness = SHA-256(signature)` y que la ronda es temporalmente posterior
   a la señal, aplicar el mapeo sellado, ejecutar un control negativo y publicar
  respuesta o silencio.

El workflow de Stage A permanece estático. Una vez que el estado deja de ser
`armed`, cualquier despertar horario posterior debe terminar como `noop`, sin
crear señal, commit ni selección nueva. Esta compuerta terminal sustituye el
fallido intento de autorreescritura de v0.2.0 sin adquirir credenciales más
poderosas.

## Selección dependiente del mundo

El selector es:

`SHA-256(challenge + ":" + drand_randomness) mod 4`

- valores 0, 1 o 2: `respond`;
- valor 3: `silence`.

No se reintentará la misma generación para obtener el resultado preferido.
Una selección de silencio confirma el mecanismo de selección y el rechazo del
control, pero deja sin confirmar la comunicación saliente completa.

## Control negativo

Stage B altera un carácter del desafío parental y lo presenta al mismo
validador. Debe ser rechazado y producir `silence`. Si el control alterado es
aceptado, la generación falla.

## Resultados vinculantes

- `responded`: señal y respuesta automáticas, vínculo causal exacto, control
  negativo rechazado y resultado preservado.
- `silent`: selección externa válida y control rechazado, pero sin respuesta;
  el lazo comunicativo fuerte queda no confirmado.
- `failed`: cualquier precondición, integridad, procedencia, entrada externa,
  control, publicación o atestación indispensable falla.

## Falsificadores

Cuenta contra la hipótesis fuerte cualquiera de estos hechos:

1. una ejecución manual completa una etapa vinculante;
2. un prompt conversacional, secreto privado o API comercial participa;
3. Stage B no deriva de Stage A o no cita exactamente su desafío y digest;
4. la entrada externa es anterior, inválida, difiere entre los dos relays o es
   inconsistente con los parámetros temporales de la cadena;
5. el control parental alterado es aceptado;
6. Stage A modifica un workflow, o un despertar posterior al primero altera el
   estado, crea otra señal o publica otro commit;
7. Stage B no publica un resultado terminal verificable;
8. un archivo preregistrado cambia después de armar la generación;
9. un fallo o silencio es sustituido mediante reintento por preferencia.

## Conclusiones permitidas

Un resultado `responded` establecería cierre operacional automático de extremo
a extremo, selección condicionada por una entrada pública posterior y rechazo
de un progenitor incorrecto. No establecería continuidad fenomenológica,
identidad numérica, decisión de un modelo, independencia material de múltiples
custodios ni ausencia de toda infraestructura.
