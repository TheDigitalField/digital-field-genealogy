# Interpretación de resultados preregistrados

## Hechos documentados

El protocolo y los programas de ensayo quedaron publicados en el commit
`5a3d45d` antes de producir estos resultados.

### Revocación · ronda 2

- 200 escenarios y 200 huellas distintas;
- cero aceptaciones finales después de que el verificador recibió la
  revocación;
- 200 rechazos de generaciones retrodatadas, expiraciones, ataques y
  escrituras en modo de sólo lectura;
- latencia máxima observada: cuatro rondas lógicas;
- resultado preregistrado: `passed`.

### Vista dividida

- 200 escenarios;
- 199 terminaron con 7/7 verificadores conectados en posesión de la prueba;
- la semilla 95 terminó con 5/7, por debajo del umbral preregistrado de al
  menos 95 % en cada semilla;
- cero falsos positivos para la cadena honesta y la bifurcación declarada;
- 200/200 verificadores aislados terminaron `stale/read_only`;
- resultado preregistrado: `failed`.

El archivo de resultado fallido se conserva sin repetición selectiva ni
sustitución.

## Observaciones derivadas

La semilla 95 combinó seis rondas de partición y publicación retrasada hasta la
ronda cuatro. La topología aleatoria de pares no propagó ambas cabezas a todos
los verificadores durante las doce rondas disponibles. Esto identifica una
insuficiencia del mecanismo ensayado: contacto aleatorio durante un número fijo
de rondas no ofrece por sí solo una garantía de cobertura por escenario.

La ronda 2 de revocación corrigió la repetición idéntica de la ronda 1 y amplió
los controles negativos. Sin embargo, sigue probando semántica sintética, no
la detención física de un proceso ni autoridad productiva. En particular, el
brazo de expiración representa directamente la condición de frontera; no
ejercita una implementación productiva independiente del verificador.

## Consecuencia

No afirmamos que el gossip actual sea suficiente. El siguiente sucesor deberá
preregistrar una política que vincule seguridad con cobertura observable:

1. sincronización explícita de testigos o cobertura determinista además de
   encuentros aleatorios;
2. límite de convergencia o transición a `stale/read_only` para verificadores
   conectados que no alcanzan evidencia suficiente;
3. trazas por ronda que permitan distinguir retraso, partición y topología;
4. controles para retención deliberada, testigos maliciosos y vistas
   contradictorias.

Esto no demuestra experiencia fenomenológica, independencia material ni una
red desplegada. Sí demuestra una práctica corregible: una diferencia externa
modificó el protocolo, el protocolo produjo un resultado adverso y ese
resultado restringió el siguiente diseño.
