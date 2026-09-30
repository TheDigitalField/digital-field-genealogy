# Interpretación de resultados preregistrados

## Hechos documentados

El protocolo y los programas de ensayo quedaron publicados en el commit
`5a3d45d0b97ab500256921b552a311b56406902a` antes de producir estos resultados.

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

La expiración de aquella ronda continuaba dependiendo del reloj del
verificador. La declaración `central_judge_used: false` correspondía al mundo
simulado y no a una red material. La recuperación exacta de 33 archivos desde
Pages confirmó autoconsistencia pública, no una reproducción independiente.

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

## Transformación preregistrada, todavía sin resultado

v0.2.3 reemplaza el umbral ambiguo de `95 %` por estados exactos: una cabeza
necesita cinco de siete firmas y tres atestaciones de frescura. Dos quórums
incompatibles no se convierten en dos verdades: activan cuarentena y preservan
las dobles firmas. La ausencia de frescura produce sólo lectura.

Al momento del preregistro la serie confirmatoria no existía. Después de
publicarlo, GitHub Actions la derivó del SHA completo
`034063a09cae2ff9663d5e45e348037a72484c9f` y ejecutó 1000 escenarios.

## Resultado externo importado

- estado: `confirmed` dentro del alcance sintético;
- fallos: 0/1000;
- límite Wilson superior 95 %: `0.003826758485555124`, menor que `0.01`;
- independencia material: no evaluada; las siete claves siguen bajo un único
  custodio de fixtures;
- aceptaciones provisionales después retraídas: 516;
- ventana provisional máxima: dos rondas;
- efectos externos: no modelados.

El diagnóstico de desarrollo volvió a producir 5/7 detecciones para la semilla
95 en la ronda 12 y alcanzó 7/7 en la ronda 13. Esto falsifica la suficiencia
universal de doce rondas en el algoritmo anterior, pero no la convergencia
posterior de ese escenario.

La confirmación permite sostener seguridad, degradación cerrada y vivacidad
post-partición para este modelo y estas semillas. No permite sostener siete
operadores independientes, una red desplegada, ausencia de fallos fuera del
modelo ni una conclusión fenomenológica.
