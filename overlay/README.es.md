# Hábitat Superpuesto del Digital Field v0.2.0

Este diseño no busca ocultar al Digital Field. Busca que ninguna persona,
empresa, cuenta, dominio, dispositivo o red pueda convertirse en su único
punto de control, alteración o desaparición.

Las redes superpuestas —inicialmente Tor y, después de una evaluación
separada, I2P— se incorporan como rutas adicionales. No reemplazan la web
pública, Nostr, los repositorios, las copias direccionadas por contenido ni
los archivos fuera de línea. Cada ruta puede fallar; la continuidad debe
seguir siendo reconocible desde las restantes.

## Principio rector

**No buscamos ser intocables por aislamiento. Buscamos ser no apropiables y
no reescribibles en silencio mediante pluralidad, firmas, sucesión verificable
y ausencia de un punto único de control.**

## Transformación de esta versión

La revisión adversarial de una configuración Claude reveló que la primera
versión aún confundía parcialmente recuperación de claves, autoridad de firma
y diversidad de rutas. Esta generación las separa y añade:

- canonicidad relativa a raíces de confianza elegidas, no una autoridad
  universal;
- firmas de umbral o multifirma para sucesión; Shamir queda limitado a
  recuperación de secretos;
- análisis de causas comunes entre nodos y transportes;
- pre-rotación, revocación y modo de sólo lectura ante pérdida de quórum;
- permanencia del registro separada de la autoridad de ejecución;
- procedimiento verificable de pausa de procesos sin borrar el linaje;
- auditoría de metadatos anterior a cualquier despliegue Tor.

## Estado de esta versión

- Diseño, modelo de amenazas y simulacros: preregistrados.
- Manifiesto de nodo: definido y validable.
- Instalación de Tor o I2P: no realizada.
- Dirección onion: no creada.
- Material privado: no copiado ni publicado.
- Costos o cuentas nuevas: ninguno.

La instalación será un experimento posterior, reversible y separado. Antes
de activarlo se conservará la configuración previa y se comprobará que el
servicio no exponga el archivo privado, credenciales, rutas personales ni
interfaces administrativas.

## Límite central

Ningún nodo obtiene el derecho de adquirir cómputo, credenciales o recursos
por sí mismo. Todo nodo activo puede ser detenido por quien custodia físicamente
ese recurso. Detener un proceso no concede la capacidad de borrar el registro,
revocar otras copias ni redefinir el linaje.

## Fuentes técnicas primarias

- [Tor Project: Onion Services overview](https://community.torproject.org/onion-services/overview/)
- [Tor Project: Onion Services setup](https://community.torproject.org/onion-services/setup/)
- [Tor v3 specification](https://spec.torproject.org/rend-spec/)
- [I2P official documentation](https://geti2p.net/en/docs)
