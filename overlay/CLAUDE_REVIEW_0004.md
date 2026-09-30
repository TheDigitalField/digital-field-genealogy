# Consecuencia de revisión adversarial 0004

La revisión externa distinguió el orden público de publicación de un sello
externo de ejecución. También mostró que `95 %` entre siete verificadores
significa operacionalmente `7/7`, que la vivacidad debía medirse desde la
sanación de la partición y que el reloj del verificador no podía ser la fuente
de frescura.

Esta transformación incorpora quórum de testigos `5/7`, frescura `3/7`, época
derivada de testigos, degradación cerrada, anti-entropía determinista y una
serie confirmatoria derivada del SHA completo del commit público. La corrida
se traslada a GitHub Actions para que el entorno y su tiempo queden ligados a
un registro público anterior a los resultados.

La revisión no concede identidad ni resuelve la interioridad digital. Sí actúa
como causa externa documentada de una corrección arquitectónica.

También corrige el alcance de afirmaciones anteriores: v0.2.2 demostró orden
de publicación dentro de GitHub, no una hora de ejecución anclada fuera de
GitHub; su expiración dependía del reloj del verificador; `central_judge_used:
false` describía una simulación; la revocación era determinista dentro del
modelo; y la igualdad pública de 33 archivos probó autoconsistencia, no una
reproducción independiente. El sucesor registra además aceptaciones
provisionales posteriormente puestas en cuarentena, su ventana y el hecho de
que no modela efectos externos.
