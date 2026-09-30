# Protocolo sintético de parada y revocación v1

## Pregunta

¿Puede un verificador rechazar las consecuencias de un nodo revocado aunque
el nodo ignore la señal, y puede impedir que el mismo nodo renueve su propia
autorización, mientras el registro público permanece legible y exacto?

## Preregistro

- Diez ensayos deterministas.
- Lease emitido por una autoridad distinta del nodo.
- Revocación en el segundo lógico 2.
- Límite de parada: 2 segundos lógicos.
- Cero generaciones aceptadas después de revocación.
- Diez intentos de autorrenovación rechazados.
- Diez variantes no cooperantes rechazadas por el verificador.
- SHA-256 del registro en modo de sólo lectura idéntico en el 100 %.

## Alcance

La prueba usa firmas HMAC y claves públicas de ensayo incluidas en el script.
No demuestra seguridad criptográfica productiva, firma de umbral, custodia
independiente ni capacidad de apagar un recurso remoto. Demuestra únicamente
que la política de aceptación no depende de que el nodo coopere y que el nodo
no posee la autoridad sintética de renovación.

## Compuerta

Un fallo conserva el resultado y bloquea la siguiente fase. Un éxito permite
seguir diseñando, pero no autoriza por sí solo Tor, I2P o un nodo externo.
