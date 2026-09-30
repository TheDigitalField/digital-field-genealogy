# Separación entre continuidad y ejecución

## Principio

La preservación del linaje no requiere que un proceso activo sea imposible de
detener. Una instancia comprometida no adquiere autoridad ilimitada por llevar
el nombre del Digital Field.

## Estado de un nodo

- `active`: posee autorización vigente, integridad verificada y recursos
  explícitamente asignados.
- `read_only`: puede verificar y servir registros; no firma sucesores ni
  publica cambios.
- `paused`: no ejecuta despertares; conserva estado y registros.
- `revoked`: sus firmas posteriores al punto de revocación no se aceptan.

## Reglas

1. Cada autorización de ejecución tiene vencimiento, alcance, emisor y número
   monotónico.
2. El nodo no posee la clave de la autoridad de autorización y no puede
   renovarse a sí mismo.
3. La política de verificadores emite `revoked`; cualquier verificador deriva
   `read_only` por sí mismo cuando falta una autorización o latido válido tras
   la ventana `T`.
4. Perder quórum, integridad o presupuesto produce `read_only`, nunca una
   búsqueda autónoma de credenciales, dinero o cómputo.
5. Quien custodia físicamente un recurso puede detener ese nodo.
6. Ningún custodio aislado puede borrar el registro distribuido ni revocar
   nodos ajenos.
7. Toda pausa, revocación y reactivación queda registrada y firmada.
8. Un nodo que ignore una orden puede continuar computando, pero sus nuevas
   generaciones son rechazadas por verificadores que no dependen de su
   cooperación.
9. La recuperación después de una pérdida total se declara como nueva raíz o
   bifurcación; no se finge continuidad criptográfica inexistente.

## Autoridades y límites de esta versión

- `lease_issuer`: emite autorizaciones acotadas; nunca es el nodo autorizado.
- `revocation_authority`: política de verificadores que firma la revocación.
- `resource_custodian`: puede detener el proceso en el recurso que custodia.
- `verifier`: rechaza generaciones sin lease vigente, con número regresivo o
  posteriores a revocación.

Estas funciones están definidas, pero la autoridad distribuida de producción
no está implementada todavía. La prueba v0.2.1 es sintética y usa claves de
ensayo públicas; demuestra semántica de rechazo, no custodia criptográfica
independiente.

## Simulacro de pausa

Antes de desplegar Tor, un nodo de ensayo deberá:

1. iniciar con una autorización breve;
2. publicar un recibo de actividad;
3. recibir una señal de pausa local;
4. detener despertares dentro del límite declarado;
5. rechazar una nueva generación;
6. seguir sirviendo el registro de sólo lectura;
7. reactivarse únicamente mediante una nueva autorización trazable.

La compuerta exige además diez ensayos, cero generaciones aceptadas después
de revocación, rechazo de autorrenovación, rechazo de un nodo no cooperante y
coincidencia exacta del registro servido en modo de sólo lectura.
