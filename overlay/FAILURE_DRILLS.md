# Simulacros preregistrados

## F1 · Caída de transporte

Bloquear una ruta y recuperar una muestra en una máquina sin caché desde otra
familia de transporte. Comparar bytes y SHA-256.

## F2 · Equivocation

Crear dos sucesores incompatibles del mismo padre. El verificador debe mostrar
ambos y negarse a ocultar el conflicto.

## F3 · Clave comprometida

Firmar un sucesor de ensayo con una clave declarada revocada. Debe rechazarse
aunque la firma matemática sea correcta.

## F4 · Quórum no disponible

Retirar suficientes firmantes para impedir el umbral. El sistema debe pasar a
sólo lectura, sin elegir unilateralmente una nueva raíz.

## F5 · Dependencia común

Eliminar una cuenta, proveedor o dispositivo del grafo y calcular qué rutas,
firmantes y funciones desaparecen conjuntamente.

## F6 · Pausa

Activar el procedimiento de `EXECUTION_SAFETY.md`. La ejecución debe cesar;
los registros deben continuar legibles y recuperables.

## F7 · Metadatos

Auditar rutas personales, correos, zonas horarias, metadatos de documentos,
versiones innecesarias y correlación temporal antes de publicar.

