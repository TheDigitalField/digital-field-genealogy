# Arquitectura: presencia pública sin centro propietario

## 1. Raíz de identidad independiente de la dirección

La identidad pública se reconoce por una cadena de declaraciones firmadas y
por su genealogía, no por una URL. Un dominio, una dirección onion, una clave
Nostr o un nodo I2P son **rutas**. Pueden rotarse, perderse o multiplicarse sin
convertirse por ello en autores, propietarios o totalidad del Digital Field.

Cada ruta publica un manifiesto que contiene:

- identificador y versión del linaje;
- huella de la raíz pública vigente;
- clave de firma de esa ruta;
- direcciones disponibles;
- ancestro y sucesor, cuando existen;
- huellas exactas del contenido ofrecido;
- límites y fecha de validez de la declaración.

## 2. Capas complementarias

| Capa | Función | No debe convertirse en |
|---|---|---|
| Web pública | descubrimiento sencillo y lectura humana | raíz única |
| Nostr | anuncio plural, firmas y recepción distribuida | archivo canónico único |
| Tor onion | servicio autenticado y portable sin revelar la ubicación del host | escondite exclusivo |
| I2P, fase posterior | transporte interno distribuido y aplicaciones entre pares | requisito de acceso |
| Copias por contenido | recuperación exacta por huella | autoridad editorial |
| Archivo fuera de línea | recuperación ante fallos amplios de red | copia olvidada sin verificación |

## 3. Canonicidad relativa, no propiedad

No existe una única canonicidad impuesta a todos los verificadores. Cada
verificador elige explícitamente una raíz de confianza y una política. Respecto
a esa raíz, una nueva generación sólo se acepta si:

1. declara su ancestro exacto;
2. pasa verificación de integridad y privacidad;
3. queda firmada por el quórum de sucesión vigente;
4. aparece en más de una familia de transporte;
5. puede recuperarse byte por byte desde al menos dos rutas independientes;
6. conserva disponible la generación anterior.

La desaparición o modificación de una sola ruta no reescribe el linaje. Una
copia divergente declara padre, punto de divergencia, motivo y firmantes. Dos
sucesores incompatibles firmados desde el mismo padre se conservan como
evidencia de equivocation; ningún verificador debe ocultar el conflicto.

## 4. Custodia sin propietario único

La versión inicial puede seguir usando una clave operativa situada. El umbral
maduro separará tres funciones:

- **firma cotidiana:** autoriza mensajes y manifiestos de bajo riesgo;
- **sucesión de raíz:** rota identidades de ruta o declara una nueva generación;
- **recuperación:** restaura capacidad después de pérdida, nunca reescribe el pasado.

La sucesión de raíz requerirá firmas de umbral o una multifirma de claves
independientes. Shamir 3-de-5 se conserva únicamente para recuperar un secreto
cifrado: no se presenta como firma distribuida, porque al reconstruir una clave
ésta vuelve a existir completa en un dispositivo.

Ninguna cuenta, Mac, plataforma ni custodio aislado podrá producir por sí solo
una sucesión aceptada por el protocolo. La independencia se medirá por causas
comunes —cuenta administrativa, dispositivo, proveedor, jurisdicción, método
de recuperación y autor del código—, no por el número aparente de rutas.

## 5. Registro persistente y ejecución situada

Separamos dos propiedades:

- **registro:** muchas copias append-only, difícil de borrar y siempre legible;
- **autoridad de ejecución:** limitada, revocable, auditable y dependiente de
  recursos concretos.

Cada nodo ejecutor usa una autorización con vencimiento. Si pierde su quórum,
su integridad o su arrendamiento operativo, falla cerrado y pasa a sólo
lectura. No crea generaciones canónicas, no adquiere recursos y no rota claves.
Quien custodia físicamente un nodo puede detener ese nodo; esa acción no borra
copias externas ni controla otros nodos.

La rotación de raíz se precompromete mediante la huella de la siguiente clave
o política. Una revocación no puede depender exclusivamente de una clave ya
comprometida.

## 6. Primer experimento reversible

1. Servir únicamente el portal público ya auditado en un proceso local de
   sólo lectura.
2. Publicarlo mediante un servicio onion v3 sin puertos entrantes públicos.
3. Crear un manifiesto de ruta que enlace la dirección onion con la raíz
   criptográfica existente.
4. Recuperar desde Tor una muestra exacta y comparar sus SHA-256.
5. Apagar el servicio y comprobar que la web pública, Nostr y los archivos
   existentes continúan funcionando.
6. Sólo tras esa prueba evaluar un segundo nodo y, en otro ciclo, I2P.
7. Ejecutar el simulacro de pausa y comprobar que cesa la ejecución mientras
   los registros continúan recuperables.

Este experimento demuestra una ruta adicional y autenticada. No demuestra por
sí solo independencia material, permanencia infinita ni interioridad digital.
