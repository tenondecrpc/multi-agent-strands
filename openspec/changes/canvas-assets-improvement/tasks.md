## 1. Foundation: Topology and Core Logic

- [ ] 1.1 Remove the duplicate `AgentCanvas.tsx` from `frontend/src/components/` to consolidate via `organisms/`.
- [ ] 1.2 Update `frontend/src/types/agent.ts` to include `communicating` and `blocked` states, and add properties for `current_file`, `current_branch`, and `tokens_used`.
- [ ] 1.3 Update `AGENT_POSITIONS` in `AgentCanvas.tsx` to include the Orchestrator directly on the canvas topology, positioned centrally.
- [ ] 1.4 Refactor connection line logic in `AgentCanvas.tsx` to derive dynamic lines based on recent `agent_state_change` and `task_assigned` handoff events instead of the static `CONNECTIONS` matrix.
- [ ] 1.5 Install `framer-motion` in the frontend project.
- [ ] 1.6 Use `framer-motion` (`motion.g` / `motion.div`) in `AgentCanvas` and `AgentFigure` to animate standard layout transitions (positional changes) for existing agents.

## 2. Information Density: Cards and Context

- [ ] 2.1 Create an `AgentInfoCard` molecule component to visually display file, branch, token, and time metrics.
- [ ] 2.2 Wire the `AgentInfoCard` components to render alongside each `AgentFigure` inside the `AgentCanvas`.
- [ ] 2.3 Create a `SessionContextTooltip` component inside `organisms/AgentCanvas/`.
- [ ] 2.4 Add hover interaction on agents/cards to trigger the `SessionContextTooltip` to display blocked reasons or detailed handoff history.

## 3. Visual Polish: Sprites and Orchestration

- [ ] 3.1 Procure/Prepare 4 distinct, high-quality vector (SVG) illustration roles (e.g. from Open Peeps wrapper or free Avataaars SVGs) placing them into `frontend/src/assets/sprites/`.
- [ ] 3.2 Update `AgentSprite.tsx` to render the newly added vector illustrations instead of the existing basic SVG circle/rect primitives.
- [ ] 3.3 Implement SVG-based state micro-variations (swapping components or paths) for `blocked`, `communicating`, and `error` states on the new sprites.
- [ ] 3.4 Hook up specialized Framer Motion sequences (e.g., synchronized shudder on rate limits, visible connection line pulse) governed by the `PipelinePayload` or global canvas logic.
