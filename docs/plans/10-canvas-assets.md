# 09. Canvas 2D Assets Improvement

> **Status**: Planned — Part of Frontend Refactoring objective

## Objective

Enhance the 2D canvas visualization system with improved agent sprites, animations, and visual effects for a more engaging monitoring dashboard.

## Current State

The MVP dashboard uses basic SVG sprites with CSS animations for agent visualization:
- Simple geometric shapes for agent figures
- Basic CSS animations (bob, pulse, shake)
- Limited visual feedback per agent state

## Improvements

### 1. Enhanced Agent Sprites

Replace basic SVG shapes with detailed pixel art animations. As part of this plan, we will source avatar assets and inspiration from the open-source repository [pixel-agents](https://github.com/pablodelucca/pixel-agents/):

| Agent | Current | Improved (Pixel Art) |
|-------|---------|----------------------|
| **Orchestrator** (Strands Agents) | Simple geometric with hat | Pixel art character orchestrating flow |
| **Backend** | Terminal icon | Pixel art character at workstation typing |
| **Frontend** | Color palette icon | Pixel art character with design tool elements |
| **QA** | Magnifying glass | Pixel art character with lab equipment or checklist |

### 2. Animation System

Upgrade from CSS animations to a proper animation state machine:

```typescript
// Animation states per agent
type AnimationState = 
  | "idle"           // Base breathing animation
  | "thinking"       // Contemplative with thought particles
  | "working"        // Active with tool-specific animations
  | "waiting"        // Patient with ambient elements
  | "success"        // Celebration with particle effects
  | "error"          // Concerned with alert indicators
  | "communicating"  // Speaking with connection lines
  | "blocked"        // Stuck with obstacle indicators
```

### 3. Canvas Rendering Improvements

```typescript
// Improved canvas rendering with proper game loop
interface CanvasConfig {
  fps: 60;
  smoothing: true;
  backgroundColor: string;
  gridOverlay: boolean;
}

// Agent rendering with layered sprites
interface AgentSprite {
  baseLayer: SVGElement;      // Body
  accessoryLayer: SVGElement; // Tools/props
  effectLayer: SVGElement;     // Particles/glow
  labelLayer: SVGElement;      // Name/task
}
```

### 4. Particle Effects

Add ambient and state-based particles:

```typescript
// Particle system for visual feedback
interface ParticleSystem {
  maxParticles: 100;
  emitOnState: ("working" | "success" | "error")[];
  particleTypes: {
    thinking: "sparkle"[];
    working: "gear"[];
    success: "confetti"[];
    error: "smoke"[];
  };
}
```

### 5. Connection Lines Enhancement

Improve agent communication visualization:

```typescript
// Animated connection lines
interface ConnectionConfig {
  color: string;
  width: number;
  dashPattern: number[];
  animationSpeed: number;
  glowEffect: boolean;
}
```

### 6. Color Palette

Unified color scheme for all agents:

| Element | Color | Usage |
|---------|-------|-------|
| **Background** | `#0f0f23` | Main canvas background |
| **Grid** | `#1a1a3e` | Subtle grid overlay |
| **Orchestrator** | `#818cf8` | Primary accent / Strands Agents |
| **Backend** | `#22c55e` | Success/working |
| **Frontend** | `#f472b6` | Creative elements |
| **QA** | `#f59e0b` | Warning/attention |
| **Error** | `#ef4444` | Error states |
| **Connections** | `#3b82f6` | Active connections |

## Implementation Steps

1. **Design System Setup**
   - Define color palette
   - Create base SVG templates
   - Set up sprite layering system

2. **Animation State Machine**
   - Implement animation controller
   - Add transition effects
   - Create easing functions

3. **Particle System**
   - Build particle emitter class
   - Add particle pool for performance
   - Implement type-specific effects

4. **Canvas Optimization**
   - Use requestAnimationFrame properly
   - Implement object pooling
   - Add off-screen rendering

5. **Integration**
   - Connect to Socket.IO events
   - Map agent states to animations
   - Add connection line animations

## File Structure

```
frontend/src/
├── components/
│   └── canvas/
│       ├── AgentCanvas.tsx      # Main canvas component
│       ├── AgentSprite.tsx      # Individual agent rendering
│       ├── ParticleSystem.ts    # Particle effects
│       ├── ConnectionLine.tsx   # Animated connections
│       └── canvas.types.ts       # TypeScript interfaces
├── hooks/
│   └── useCanvasRenderer.ts     # Canvas rendering hook
├── assets/
│   └── sprites/
│       ├── orchestrator.svg
│       ├── backend.svg
│       ├── frontend.svg
│       └── qa.svg
└── styles/
    └── canvas-animations.css    # CSS animation definitions
```

## Dependencies

```bash
# No new dependencies required
# Uses vanilla Canvas API + SVG
# Optional: GSAP for complex animations (future)
```

## Reference

- [Pixel Agents](https://github.com/pablodelucca/pixel-agents) — VS Code extension with pixel art office visualization
- [Canvas Animation Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
- [SVG Animation](https://developer.mozilla.org/en-US/docs/Web/SVG/SVG_animation_with_SMIL)
