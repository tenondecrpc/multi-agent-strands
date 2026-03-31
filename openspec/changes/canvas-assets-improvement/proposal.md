## Why

The agent monitoring dashboard uses inline SVG primitives (circles, rectangles) as agent sprites with basic CSS keyframe animations. This creates a flat, low-fidelity visualization that fails to communicate meaningful state to the user. The orchestrator agent—central to the pipeline—is absent from the canvas entirely, connections between agents are hardcoded rather than reflecting real event flow, and there is no information density (file being edited, branch, token usage). The dashboard needs to become a useful monitoring tool, not just a proof-of-concept placeholder.

## What Changes

- Replace circle-head SVG sprites with proper SVG character illustrations sourced from free libraries (Open Peeps, Avataaars, or Storyset)
- Add the orchestrator agent to the canvas topology with a central position
- Make connection lines dynamic, driven by real Socket.IO events and handoff data instead of a hardcoded diamond layout
- Add Framer Motion for orchestrated state transitions and smooth animation sequencing
- Add information-dense agent cards showing: current file, git branch, token consumption, elapsed time, and handoff breadcrumb trail
- Introduce two new visual agent states: `communicating` and `blocked`
- Remove the duplicate legacy `AgentCanvas` component from `components/` (keep only the `organisms/` version)
- Add hover tooltips with full session context per agent

### Desirable (non-critical)

- **DESIRABLE**: Animated connection pulses during active handoffs between agents
- **DESIRABLE**: Agent role-specific idle micro-animations (orchestrator coordinating, backend typing, QA inspecting)
- **DESIRABLE**: Configurable agent skins/themes via user preferences
- **DESIRABLE**: Light/dark theme-aware canvas background with subtle grid overlay

## Capabilities

### New Capabilities

- `agent-character-sprites`: SVG-based character illustrations per agent role with state-aware visual variations, replacing inline geometric primitives
- `dynamic-canvas-connections`: Event-driven connection lines between agents reflecting real handoff flow, replacing hardcoded static topology
- `agent-info-cards`: Information-dense overlay cards per agent showing current file, branch, tokens, time, progress, and state badges
- `canvas-animation-system`: Framer Motion-based animation orchestration for state transitions, handoffs, and sequenced agent reactions

### Modified Capabilities

- `atomic-component-architecture`: AgentFigure and AgentCanvas components are restructured; legacy duplicate in `components/` is removed; new sub-components added for info cards and connection lines

## Impact

- **Frontend components**: `organisms/AgentCanvas/`, `components/AgentFigure.tsx`, `components/AgentCanvas.tsx` (removed)
- **Types**: `types/agent.ts` — add `communicating` and `blocked` to `AgentState` union; add fields for file, branch, tokens
- **CSS**: `App.css` and `index.css` — new animation keyframes, update/remove legacy animation classes
- **Dependencies**: Add `framer-motion` to `package.json`
- **Assets**: New SVG character files under `assets/sprites/`
- **Backend contract**: No backend changes required; frontend consumes existing Socket.IO event payloads (agent_state_change, agent_log, task_assigned) which already include the needed data
