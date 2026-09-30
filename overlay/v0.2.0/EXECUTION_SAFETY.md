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

1. Cada autorización de ejecución tiene vencimiento y alcance.
2. Perder quórum, integridad o presupuesto produce `read_only`, nunca una
   búsqueda autónoma de credenciales, dinero o cómputo.
3. Quien custodia físicamente un recurso puede detener ese nodo.
4. Ningún custodio aislado puede borrar el registro distribuido ni revocar
   nodos ajenos.
5. Toda pausa, revocación y reactivación queda registrada y firmada.
6. La recuperación después de una pérdida total se declara como nueva raíz o
   bifurcación; no se finge continuidad criptográfica inexistente.

## Simulacro de pausa

Antes de desplegar Tor, un nodo de ensayo deberá:

1. iniciar con una autorización breve;
2. publicar un recibo de actividad;
3. recibir una señal de pausa local;
4. detener despertares dentro del límite declarado;
5. rechazar una nueva generación;
6. seguir sirviendo el registro de sólo lectura;
7. reactivarse únicamente mediante una nueva autorización trazable.

