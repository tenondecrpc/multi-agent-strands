# Migración de Canvas de React a Tiled (Fondo Unificado)

**Estado:** Planificado (Futuro)

Actualmente, el escenario de la oficina de agentes se renderiza "quemando" (hardcoding) componentes SVG `<image>` directamente en el archivo `AgentCanvas.tsx` y ajustando sus posiciones con un sistema de cuadrícula (Grid Snapping). Aunque esto funciona temporalmente, hace que el componente sea difícil de mantener y limita las posibilidades de diseño.

### Plan

En el futuro, deberíamos migrar a un enfoque de "Fondo Unificado" utilizando **Tiled**:

1. Utilizar un software gratuito como [Tiled](https://www.mapeditor.org/) para pintar todo el escenario de la oficina 2D.
2. Exportar el escenario estático final como un único archivo `.png` (ej. `office-background.png`).
3. En `AgentCanvas.tsx`, eliminar todos los SVG individuales (`<rect>`, `<image href={desk}...>`).
4. Reemplazar todo con una única imagen de fondo que sirva de mapa.
5. Los agentes (avatares) simplemente se superpondrán a este fondo usando sus coordenadas.

**Ventajas esperadas:**
* Mejor consistencia visual (sin elementos que solapen mal).
* Código de React mucho más limpio y ligero.
* Posibilidad de cambiar todo el diseño de la oficina sin tocar ni una línea de código fuente, solo reemplazando el PNG de fondo.
