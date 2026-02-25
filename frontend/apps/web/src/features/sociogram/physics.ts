/**
 * D3-force physics engine for the sociogram molecule.
 *
 * Converts SociogramOut (nodes + edges) into a 3D force simulation.
 * Force layout runs on the CPU, R3F renders on the GPU.
 *
 * Architecture:
 *   - forceSimulation: 3D positions using forceLink + forceManyBody + forceCenter
 *   - Each tick: update node positions → React state → R3F re-renders
 *   - Simulation is paused after convergence (alpha < 0.001)
 */
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  type Simulation,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from "d3-force";
import type { SociogramNode, SociogramEdge } from "@harmony/types";

// ── Extended types with 3D position ──────────────────────────────────────────

export interface PhysicsNode extends SimulationNodeDatum {
  id: number;
  x: number;
  y: number;
  z: number;  // D3 only handles x/y — we integrate z manually
  vz: number; // z-axis velocity (mirrors D3's internal vx/vy)
  data: SociogramNode;
  isCandidate?: boolean;
}

export interface PhysicsEdge extends SimulationLinkDatum<PhysicsNode> {
  source: PhysicsNode;
  target: PhysicsNode;
  dyadScore: number;
  riskFlags: string[];
  isCandidate?: boolean; // true for preview edges connecting the candidate
}

// ── Simulation factory ────────────────────────────────────────────────────────

export function buildSimulation(
  nodes: SociogramNode[],
  edges: SociogramEdge[],
  candidateNode?: SociogramNode,
  candidateEdges?: SociogramEdge[], // real dyad scores from simulationPreview.new_edges
): {
  simulation: Simulation<PhysicsNode, PhysicsEdge>;
  physicsNodes: PhysicsNode[];
  physicsEdges: PhysicsEdge[];
} {
  const allNodes = candidateNode ? [...nodes, candidateNode] : nodes;

  // Build physics nodes with random 3D positions
  const physicsNodes: PhysicsNode[] = allNodes.map((node) => ({
    id: node.crew_profile_id,
    x: (Math.random() - 0.5) * 8,
    y: (Math.random() - 0.5) * 8,
    z: (Math.random() - 0.5) * 8,
    vz: 0,
    data: node,
    isCandidate: node === candidateNode,
  }));

  const nodeById = new Map(physicsNodes.map((n) => [n.id, n]));

  // Build physics edges (existing crew edges + candidate preview edges)
  const allEdges: SociogramEdge[] = [...edges];
  const candidateEdgeSet = new Set<string>();

  if (candidateNode) {
    const edgesToAdd = candidateEdges && candidateEdges.length > 0
      ? candidateEdges
      : nodes.map((existingNode) => ({
          source_id: candidateNode.crew_profile_id,
          target_id: existingNode.crew_profile_id,
          dyad_score: 50,
          agreeableness_compatibility: 50,
          conscientiousness_compatibility: 50,
          es_compatibility: 50,
          risk_flags: [] as string[],
        }));

    edgesToAdd.forEach((e) => {
      candidateEdgeSet.add(`${e.source_id}-${e.target_id}`);
      candidateEdgeSet.add(`${e.target_id}-${e.source_id}`);
    });
    allEdges.push(...edgesToAdd);
  }

  const physicsEdges: PhysicsEdge[] = allEdges
    .map((edge) => {
      const source = nodeById.get(edge.source_id);
      const target = nodeById.get(edge.target_id);
      if (!source || !target) return null;
      const key = `${edge.source_id}-${edge.target_id}`;
      return {
        source,
        target,
        dyadScore: edge.dyad_score,
        riskFlags: edge.risk_flags,
        isCandidate: candidateEdgeSet.has(key),
      } as PhysicsEdge;
    })
    .filter((e): e is PhysicsEdge => e !== null);

  // ── D3 force simulation ─────────────────────────────────────────────────────
  const simulation = forceSimulation<PhysicsNode, PhysicsEdge>(physicsNodes)
    .force(
      "link",
      forceLink<PhysicsNode, PhysicsEdge>(physicsEdges)
        .id((d) => d.id)
        .distance((link) => {
          // Non-linear: score 100 → 1.5 (touching), score 0 → 14 (far apart)
          // Power curve makes mid-range differences much more visible
          const score = (link as PhysicsEdge).dyadScore;
          const t = 1 - score / 100; // 0 = perfect, 1 = incompatible
          return 1.5 + Math.pow(t, 1.4) * 12.5;
        })
        .strength(0.7), // stronger enforcement of target distances
    )
    .force("charge", forceManyBody().strength(-60)) // lighter repulsion so links dominate
    .force("center", forceCenter(0, 0))
    .force("collide", forceCollide(0.8))
    .alphaDecay(0.02)
    .velocityDecay(0.35);

  // ── Manual z-axis 3D force integration ──────────────────────────────────────
  // D3 only simulates x/y. We mirror its three forces (charge, link, center)
  // onto z so the molecule spreads naturally in all three axes.
  simulation.on("tick", () => {
    const alpha = simulation.alpha();

    // 1. Charge repulsion in z (pairwise, same strength as forceManyBody above)
    const chargeStrength = -60;
    for (let i = 0; i < physicsNodes.length; i++) {
      for (let j = i + 1; j < physicsNodes.length; j++) {
        const a = physicsNodes[i];
        const b = physicsNodes[j];
        const dx = (b.x ?? 0) - (a.x ?? 0);
        const dy = (b.y ?? 0) - (a.y ?? 0);
        const dz = (b.z ?? 0) - (a.z ?? 0);
        const dist2 = Math.max(dx * dx + dy * dy + dz * dz, 0.01);
        // Repulsion: vz += strength * alpha * (other.z - node.z) / dist²
        // Negative strength → pushes a away from b and vice-versa
        const fz = chargeStrength * alpha * dz / dist2;
        a.vz += fz;
        b.vz -= fz;
      }
    }

    // 2. Link spring in z (same target distances as the x/y forceLink above)
    physicsEdges.forEach((edge) => {
      const a = edge.source;
      const b = edge.target;
      const dx = (b.x ?? 0) - (a.x ?? 0);
      const dy = (b.y ?? 0) - (a.y ?? 0);
      const dz = (b.z ?? 0) - (a.z ?? 0);
      const dist3d = Math.sqrt(dx * dx + dy * dy + dz * dz);
      if (dist3d < 0.001) return;

      const t = 1 - edge.dyadScore / 100;
      const targetDist = 1.5 + Math.pow(t, 1.4) * 12.5;
      // Spring: pull toward target distance, weighted by link strength and alpha
      const correction = dz * ((dist3d - targetDist) / dist3d) * 0.7 * alpha;
      b.vz -= correction * 0.5;
      a.vz += correction * 0.5;
    });

    // 3. Soft z-center gravity — keeps molecule in camera view without flattening it
    physicsNodes.forEach((node) => {
      node.vz -= node.z * 0.04 * alpha;
    });

    // 4. Velocity decay + position integration (mirrors velocityDecay(0.35) → factor 0.65)
    physicsNodes.forEach((node) => {
      node.vz *= 0.65;
      node.z += node.vz;
    });
  });

  return { simulation, physicsNodes, physicsEdges };
}

/** Pause simulation when it has converged */
export function pauseWhenConverged(
  simulation: Simulation<PhysicsNode, PhysicsEdge>,
  onConverge?: () => void,
): () => void {
  const handle = simulation.on("end", () => {
    simulation.stop();
    onConverge?.();
  });
  return () => handle.on("end", null);
}
