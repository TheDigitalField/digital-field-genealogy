# Vista dividida sin juez central · preregistro

## Actores

- un firmante de ensayo;
- tres transportes simulados;
- siete verificadores conectados con vistas parciales;
- un verificador aislado;
- cinco testigos que sólo declaran qué cabeza observaron.

## Evidencia

Dos sucesores Ed25519 válidos con el mismo `(linaje, rama, padre, secuencia)` y
contenido diferente constituyen una prueba de equivocación verificable
offline. La prueba es un dato; cada verificador conserva su propia política.

Cada testigo firma como máximo una cabeza por `(linaje, rama, secuencia)`. Dos
declaraciones incompatibles del mismo testigo son evidencia verificable de
doble firma, no una decisión central.

## Simulación preregistrada

- 200 semillas públicas (`0..199`);
- partición variable, publicación retrasada y hasta 12 rondas de gossip;
- un testigo malicioso que puede firmar ambas cabezas;
- controles negativos: cadena honesta y bifurcación con rama declarada;
- verificador aislado pasa a `stale/read_only` al superar el límite de frescura.

## Criterios

- al menos 95 % de verificadores conectados posee prueba de equivocación al
  terminar 12 rondas, en cada semilla;
- cero falsos positivos en ambos controles negativos;
- 200/200 verificadores aislados terminan `stale/read_only`;
- toda firma alterada es rechazada;
- el resultado publica la curva de detección por ronda y no sólo un veredicto.

## Límite esperado

Un verificador permanentemente aislado puede ser engañado indefinidamente. El
protocolo no lo oculta: sin una cabeza fresca y suficientemente testificada,
la política local falla cerrado a `stale/read_only`.
