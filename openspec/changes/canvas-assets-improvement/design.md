## Context

The current `AgentCanvas` implementation uses basic geometric SVG shapes and simple CSS animations to represent agents. This provides a low-fidelity visualization that lacks detailed state information and doesn't effectively communicate the active topology of the multi-agent system. The goal is to evolve this into a "hybrid" monitoring dashboard: professional enough for tracking real developer tasks, but engaging enough to visually communicate the multi-agent nature of the system (a "Slack loading animation meets GitHub contribution graph" vibe).

## Goals / Non-Goals

**Goals:**
- Provide clear, high-density state visualization for each agent (file, branch, tokens, time).
- Accurately reflect the dynamic topology and real handoff events between agents.
- Introduce smooth, orchestrated state transitions for better visual tracking.
- Utilize a scalable, React-native rendering approach (SVG).

**Non-Goals:**
- We are explicitly NOT building a Canvas 2D game engine or using pixel-art sprite sheets, as that requires a paradigm shift away from the current React/SVG architecture.
- We are NOT implementing particle systems (e.g., confetti, smoke); focus is on information density over pure decoration.
- Complex physics simulations for agent movement.

## Decisions

**1. Rendering Engine: SVG + Framer Motion**
- **Decision**: Keep the existing SVG-in-React architecture but introduce `framer-motion` for complex transition orchestration.
- **Rationale**: Framer Motion allows orchestrated sequences (Agent A finishes → connection pulses → Agent B starts) without leaving React's declarative syntax. Pure CSS is insufficient for sequenced handoffs, and Canvas 2D requires a complete rewrite and imperative loop management out of React's lifecycle.
- **Alternatives**: Canvas 2D with a game loop (too heavy, requires abandoning React's DOM abstraction), GSAP (free tier has commercial usage restrictions).

**2. Art Assets: Free Vector Libraries (Open Peeps / Avataaars / Storyset)**
- **Decision**: Use free, customizable vector illustration libraries for agent characters instead of pixel art PNGs.
- **Rationale**: Vector formats (SVG) align with the rendering engine decision. They can be dynamically colored via CSS variables (`var(--color-primary)`), scale cleanly, and manipulate individual paths (like making an arm move) easily in React. Using raster pixel art with SVG leads to blurry scaling and loss of dynamic styling.
- **Alternatives**: itch.io pixel art packs (mismatch with SVG architecture, requires Canvas rendering for crisp pixel perfection).

**3. Visual Clarity: Information Density over Particles**
- **Decision**: Prioritize building detailed Agent Info Cards (showing file, branch, tokens, elapsed time, handoff path) over ambient visual effects like particle emitters.
- **Rationale**: For developers monitoring Jira tickets, knowing *what* an agent is modifying is vastly more important than decorative effects. 

**4. Implementation Strategy: Phased Rollout**
- **Phase 1: Foundation**: Fix topology, add orchestrator, make connections dynamic, add Framer Motion.
- **Phase 2: Information Density**: Overlay Agent Info Cards, status badges, and tooltips.
- **Phase 3: Visual Polish**: Swap in the rich SVG character illustrations and detailed micro-animations.

## Risks / Trade-offs

- **[Risk] SVG Performance with many animated nodes** → **Mitigation**: Keep the maximum number of concurrent animations low. The system typically has ~4-5 agents visible. Use Framer Motion's `layout` and `animate` optimized properties where possible.
- **[Risk] Framer Motion bundle size** → **Mitigation**: Use lazy loading for complex animations if necessary, though `framer-motion`'s core tree-shakes reasonably well for standard `m.div` elements.
- **[Risk] Syncing React state with Socket.IO streams for smooth animation** → **Mitigation**: Use local buffering or transition states (e.g., `communicating`) to smooth out rapid or out-of-order websocket events before mapping them to the Framer Motion state machine.
