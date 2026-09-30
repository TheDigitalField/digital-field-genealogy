# Parada y revocación · ronda 2 preregistrada

## Motivo

La ronda 1 repitió un único escenario diez veces. Esta ronda separa escenarios
mediante 200 semillas públicas (`0..199`) y sustituye HMAC por Ed25519 de ensayo.

## Brazos obligatorios por semilla

1. revocación con retraso de propagación variable;
2. generación retrodatada desde una cabeza anterior;
3. vencimiento del lease sin mensaje de revocación;
4. uno de cuatro ataques rotatorios: vencimiento editado, lease de otro nodo,
   escalada de alcance o firma de una autoridad obsoleta;
5. intento de escritura en `read_only` seguido de comparación SHA-256;
6. revaluación por el verificador retrasado después de recibir la revocación.

## Criterios fijados antes de ejecutar

- 200 huellas de escenario distintas;
- cero generaciones finalmente aceptadas después de conocer la revocación;
- 200/200 expiraciones sin revocación rechazadas;
- 200/200 ataques de renovación o alcance rechazados;
- 200/200 escrituras en sólo lectura rechazadas, con hash intacto;
- 200/200 generaciones retrodatadas rechazadas después de propagación;
- latencia de efecto de revocación igual al retraso preregistrado, máximo 4
  rondas lógicas.

## Límite

Es una simulación de verificadores y no detiene procesos físicos. Las claves
privadas de ensayo son públicas. El resultado puede demostrar semántica de
política y controles negativos, no autoridad criptográfica productiva.
