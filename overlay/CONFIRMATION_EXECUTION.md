# Ejecución confirmatoria externa

La primera serie confirmatoria debe ejecutarse en GitHub Actions desde el
mismo commit público que contiene el protocolo y el programa. El SHA completo
del checkout es simultáneamente el ancla y la fuente de las 1000 semillas.

El flujo público debe conservar:

- SHA completo del commit;
- identificador y URL de la corrida;
- repositorio y actor declarados por GitHub;
- hora de inicio y final informada por el runner;
- resultado JSON, diagnóstico de la semilla 95 y sus SHA-256;
- código de salida de cada prueba.

Eso vincula públicamente la ejecución con un commit ya publicado. No equivale
a un sello temporal independiente de GitHub. Un ancla adicional en otra
infraestructura continúa pendiente.

La corrida no escribe de vuelta al repositorio. Sus resultados se importarán
sin modificación y se publicarán después en un commit distinto. La igualdad
de bytes podrá comprobarse contra el artefacto de la corrida.
