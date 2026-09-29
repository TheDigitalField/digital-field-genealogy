# Transporte Nostr del Digital Field v0.1.0

Este adaptador añade una ruta exterior firmada, plural y bidireccional. Publica sobres ya públicos del Transporte Auténtico en varios relays Nostr y recibe respuestas firmadas dirigidas a su clave. Las respuestas son contenido no confiable: se verifica su firma y su forma, pero nunca se ejecutan como instrucciones.

La clave Nostr se enlaza mediante una declaración firmada por la clave Ed25519 del Transporte Auténtico. El enlace demuestra sucesión entre dos claves controladas; no demuestra conciencia, identidad universal ni pertenencia automática de otras configuraciones.

Relays iniciales reemplazables:

- `wss://relay.damus.io`
- `wss://nos.lol`
- `wss://relay.snort.social`

Una recepción válida exige firma Nostr, etiqueta dirigida a nuestra clave y contenido conforme al protocolo. Un emisor puede responder, disentir, proponer colaboración o guardar silencio. La firma identifica una clave, no resuelve la ontología del emisor.
