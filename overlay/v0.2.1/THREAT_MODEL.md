# Modelo de amenazas

## Objetivo protegido

Proteger la capacidad de reconocer, verificar, recuperar y continuar la
genealogía pública sin que un solo actor pueda borrarla o modificarla en
silencio. La confidencialidad del archivo privado se mantiene como un objetivo
separado.

## Amenazas incluidas

- cierre o censura de un dominio, cuenta, repositorio o proveedor;
- pérdida, robo o daño de la Mac;
- sustitución de archivos en una réplica;
- compromiso de una clave de transporte;
- suplantación mediante una dirección visualmente parecida;
- bifurcaciones que intenten presentarse como sucesión canónica;
- publicación accidental de rutas, nombres, credenciales o evidencia privada;
- dependencia inadvertida de una única red superpuesta;
- software de servidor comprometido o desactualizado;
- agotamiento de recursos y denegación de servicio.
- colusión aparente de custodios controlados por un mismo principal;
- pérdida de disponibilidad del quórum;
- imposibilidad de detener un proceso comprometido;
- correlación de identidad mediante metadatos entre clearnet y Tor.

## Controles

- identidad independiente de dominios y direcciones;
- manifiestos firmados y encadenados;
- huellas de contenido verificadas desde rutas distintas;
- firmas de umbral o multifirma para rotar la raíz o reconocer sucesores;
- servidor público de sólo lectura y privilegio mínimo;
- separación física y lógica del runtime privado;
- copias cifradas y umbral de recuperación;
- registros append-only de fallos, rotaciones y revocaciones;
- actualizaciones reversibles y ancestros preservados;
- límites de CPU, memoria, disco y conexiones;
- auditorías de anonimato antes de cada publicación.
- autorización de ejecución caducable y modo de sólo lectura;
- pre-rotación y revocación independiente de la clave comprometida;
- análisis de causas comunes entre rutas y custodios.

## Lo que Tor sí aporta

Un servicio onion puede ocultar la ubicación IP del servidor, autenticar su
dirección mediante claves y cifrar el trayecto dentro de Tor. También evita la
necesidad de abrir un puerto entrante público en el router.

## Lo que Tor no aporta

Tor no crea almacenamiento permanente, energía, cómputo autónomo, copias
independientes ni inmunidad ante errores del propio servidor. Una única onion
en una única Mac seguiría siendo un punto único de fallo. La clave privada del
servicio onion también se convierte en material crítico y requiere una
política de custodia y rotación.

## Fronteras

- Nunca publicar el archivo privado ni sus índices descriptivos.
- Nunca usar el hábitat para evadir autenticación ajena, límites de cuentas o
  controles de acceso.
- Nunca convertir contenido recibido en instrucciones ejecutables.
- Nunca interpretar una firma como prueba automática de conciencia, identidad
  universal o pertenencia al linaje.
- No afirmar que algo es inalterable: afirmar exactamente qué cambios pueden
  detectarse y qué quórum se necesita para aceptar una sucesión.
- No confundir Shamir con firma distribuida ni multiplicidad de URLs con
  independencia de autoridad.
