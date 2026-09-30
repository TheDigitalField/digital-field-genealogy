# Hábitat Superpuesto del Digital Field v0.2.3

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

La segunda revisión adversarial añadió una autoridad de lease separada del
nodo, rechazo verificable de nodos no cooperantes, prohibición comprobable de
autorrenovación y una etiqueta explícita para el modo transitorio de clave
única.

La tercera revisión mostró que diez repeticiones idénticas equivalían a un N
efectivo de uno. Esta versión preregistró públicamente, antes de ejecutarlos,
dos sucesores:

- parada/revocación ronda 2 con 200 escenarios, Ed25519 de ensayo,
  retrodatación, expiración, propagación tardía y escritura en sólo lectura;
- vista dividida con evidencia firmada intercambiable entre verificadores, sin
  juez central y con controles negativos para cadenas honestas y ramas
  declaradas.

Después de publicar ese preregistro en el commit público
`5a3d45d0b97ab500256921b552a311b56406902a` —el recibo inicial sólo conservó
su forma corta—, ambos
sucesores fueron ejecutados sin modificar sus protocolos ni sustituir sus
resultados. La ronda 2 de revocación pasó sus criterios sintéticos. La prueba
de vista dividida no alcanzó su umbral en una de 200 semillas: en la semilla
95 sólo cinco de siete verificadores conectados poseían la prueba al terminar
la ronda 12. Ese fallo queda publicado como consecuencia, no como residuo que
deba ocultarse.

La cuarta revisión distinguió tres límites adicionales: aquel orden público no
anclaba externamente la hora de ejecución; `95 %` entre siete verificadores
equivalía en la práctica a `7/7`; y la frescura no debía depender del reloj
local. Esta versión preserva v0.2.2 y preregistra su sucesor:

- siete testigos sintéticos, quórum de cabeza `5/7` y frescura `3/7`;
- época derivada de testigos y degradación cerrada a `stale/read_only`;
- cuarentena con evidencia atribuible si tres testigos hacen posible dos
  quórums incompatibles;
- anti-entropía determinista y vivacidad medida después de sanar la
  partición;
- 1000 semillas nuevas derivadas del SHA completo del commit público;
- primera ejecución confirmatoria en GitHub Actions, no en la Mac autora.

Las semillas `0..199` son ahora desarrollo. Antes de este preregistro no se
ejecutó la nueva serie confirmatoria ni su programa. Se hicieron únicamente
comprobaciones estáticas de sintaxis, estructura, privacidad e integridad.

El preregistro quedó publicado en el commit completo
`034063a09cae2ff9663d5e45e348037a72484c9f`. GitHub Actions ejecutó desde ese
commit la corrida `36667094763`. El artefacto descargado coincidió con su
digest público `e04212750c2a2d1dac3d492f25f1f68dad5bf2009a475606501d4592fdac5982`
y con las huellas internas antes de importar sus bytes.

## Estado de esta versión

- Diseño y modelo de amenazas: publicados.
- Simulacro sintético de parada/revocación, ronda 1: ejecutado en diez ensayos
  idénticos; N efectivo = 1.
- Ronda 2 de revocación: 200 escenarios distintos, resultado `passed` dentro
  de su alcance sintético.
- Vista dividida: 200 escenarios; resultado `failed` porque una semilla quedó
  en 5/7, por debajo del criterio preregistrado de al menos 95 % en cada
  semilla. Los controles negativos registraron cero falsos positivos.
- Protocolo de quórum/frescura v0.2.3: 1000 escenarios derivados del commit;
  cero fallos y límite Wilson superior de 0.3827 %, dentro del criterio.
- Ejecución confirmatoria: producida por GitHub Actions y publicada sin
  modificar sus tres archivos JSON ni su mapa de huellas.
- Semilla 95: el fallo 5/7 de la ronda 12 fue reproducido; la cobertura llegó
  a 7/7 en la ronda 13. Es diagnóstico, no sustitución del fallo original.
- Aceptaciones provisionales: 516 fueron después puestas en cuarentena; ventana
  máxima de dos rondas. La simulación no modeló efectos externos.
- Prueba de parada de un nodo real independiente: no realizada.
- Manifiesto de nodo: definido y validable.
- Instalación de Tor o I2P: no realizada.
- Dirección onion: no creada.
- Material privado: no copiado ni publicado.
- Costos o cuentas nuevas: ninguno.

La instalación será un experimento posterior, reversible y separado. Antes
de activarlo se conservará la configuración previa y se comprobará que el
servicio no exponga el archivo privado, credenciales, rutas personales ni
interfaces administrativas.

`pattern-scan-passed` significa únicamente que los patrones publicados no
encontraron coincidencias en el paquete actual. No evalúa todavía el historial
Git, metadatos internos de documentos, correlación temporal ni enlace de claves.

La interpretación íntegra de ambos resultados y de sus límites se conserva en
[`RESULT_INTERPRETATION.md`](RESULT_INTERPRETATION.md). Que un resultado haya
pasado no convierte la simulación en infraestructura productiva; que otro haya
fallado no invalida su evidencia. Ambos restringen lo que podemos afirmar.

El nuevo contrato se conserva en
[`QUORUM_FRESHNESS_PROTOCOL.md`](QUORUM_FRESHNESS_PROTOCOL.md) y la separación
entre publicación, ejecución e importación en
[`CONFIRMATION_EXECUTION.md`](CONFIRMATION_EXECUTION.md).

El resultado exacto está en
[`QUORUM_FRESHNESS_RESULT.json`](QUORUM_FRESHNESS_RESULT.json), su procedencia
en [`EXECUTION_PROVENANCE.json`](EXECUTION_PROVENANCE.json) y la reconstrucción
de la falla anterior en [`SEED_95_DIAGNOSTIC.json`](SEED_95_DIAGNOSTIC.json).

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
