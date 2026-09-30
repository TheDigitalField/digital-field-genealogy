# Auditoría anterior a una ruta Tor

Tor protege propiedades del transporte; no limpia los documentos publicados.
Antes de desplegar una ruta onion se inspeccionarán:

- rutas absolutas de directorios personales y nombres de cuentas;
- correos, teléfonos, identificadores y nombres personales;
- metadatos EXIF, PDF, Office y recursos extendidos;
- autor y desfase horario del historial Git;
- versiones de software que no sean necesarias para reproducibilidad;
- claves públicas que enlacen identidades entre transportes;
- cercanía temporal entre publicaciones onion y clearnet;
- hashes de material privado susceptible de confirmación por diccionario;
- registros, errores y mapas de origen incrustados.

Un hallazgo bloquea el despliegue hasta que sea eliminado, aceptado como
divulgación pública deliberada o contenido en una capa separada.
