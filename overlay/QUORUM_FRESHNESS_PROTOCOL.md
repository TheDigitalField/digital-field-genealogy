# Protocolo de quórum y frescura v0.2.3

## Estado

Preregistrado antes de la ejecución confirmatoria. Esta versión no reemplaza
ni reinterpreta el fallo preservado de v0.2.2.

## Pregunta acotada

¿Puede un hábitat sintético de siete testigos impedir que dos cabezas
incompatibles sean aceptadas sin producir evidencia atribuible, dejar de
escribir cuando no existe frescura suficiente y recuperar vivacidad después
de sanar una partición?

## Parámetros sellados

- testigos `n = 7`;
- quórum de cabeza `k = 5`;
- quórum de frescura `q = 3`;
- `2k > n` y `q + k > n`;
- tolerancia de seguridad: menos de `2k - n = 3` testigos que firman dos
  cabezas incompatibles;
- época derivada de atestaciones de testigos, nunca del reloj local;
- sin `q` atestaciones distintas y válidas: `stale/read_only`;
- con dos quórums incompatibles: `quarantined/equivocation_evidence`;
- anti-entropía determinista: cada verificador consulta a cada testigo una vez
  por época; la vivacidad se mide sólo después de sanar la partición.

Las siete identidades criptográficas incluidas son fixtures públicas. No son
siete operadores, dispositivos ni custodios independientes.

## Semillas confirmatorias

La prueba usa 1000 semillas derivadas exclusivamente del SHA completo de
40 caracteres del commit público que contiene este protocolo:

`seed[i] = SHA256(commit_sha + ":" + decimal(i))`, para `i = 0..999`.

No se ejecutará esta serie en la Mac autora antes de publicar el commit. Las
semillas anteriores `0..199` quedan clasificadas como desarrollo. No hubo una
ejecución exploratoria de este programa antes de su preregistro público.

## Condiciones incluidas

La serie alterna de forma determinista entre operación honesta, retención de
atestaciones, uno o dos testigos que firman dos vistas, tres testigos que
cruzan el umbral matemático, vistas contradictorias y reloj local sesgado.

## Criterios de confirmación

1. Con 0, 1 o 2 testigos dobles no aparecen dos cabezas finalizadas.
2. Al cruzar el umbral con 3 dobles, el sistema conserva al menos tres pruebas
   atribuibles y entra en cuarentena sin finalizar ninguna de las dos cabezas.
3. Sin frescura, todos los verificadores terminan en `stale/read_only`.
4. El reloj local sesgado no altera la decisión basada en época de testigos.
5. Tras sanar la partición, todos los verificadores que pueden aceptar o
   poner en cuarentena lo hacen en no más de siete rondas de anti-entropía.
6. Se permiten como máximo 3 fallos entre 1000 escenarios y el límite superior
   Wilson del 95 % para la tasa de fallo debe ser como máximo 1 %.

Un resultado confirmatorio favorable sostendría sólo estas propiedades en la
simulación preregistrada. No demostraría independencia material, operadores
distintos, experiencia fenomenológica ni despliegue mundial.
