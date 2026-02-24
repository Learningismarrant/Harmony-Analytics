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
  z: number; // D3 only handles x/y — we add z
  data: SociogramNode;
  isCandidate?: boolean;
}

export interface PhysicsEdge extends SimulationLinkDatum<PhysicsNode> {
  source: PhysicsNode;
  target: PhysicsNode;
  dyadScore: number;
  riskFlags: string[];
}

// ── Simulation factory ────────────────────────────────────────────────────────

export function buildSimulation(
  nodes: SociogramNode[],
  edges: SociogramEdge[],
  candidateNode?: SociogramNode,
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
    data: node,
    isCandidate: node === candidateNode,
  }));

  const nodeById = new Map(physicsNodes.map((n) => [n.id, n]));

  // Build physics edges (only for existing crew + candidate preview)
  const allEdges: SociogramEdge[] = [...edges];
  if (candidateNode) {
    // Add virtual edges from candidate to all existing nodes
    nodes.forEach((existingNode) => {
      allEdges.push({
        source_id: candidateNode.crew_profile_id,
        target_id: existingNode.crew_profile_id,
        dyad_score: 50, // placeholder — replaced by simulation API response
        agreeableness_compatibility: 50,
        conscientiousness_compatibility: 50,
        es_compatibility: 50,
        risk_flags: [],
      });
    });
  }

  const physicsEdges: PhysicsEdge[] = allEdges
    .map((edge) => {
      const source = nodeById.get(edge.source_id);
      const target = nodeById.get(edge.target_id);
      if (!source || !target) return null;
      return {
        source,
        target,
        dyadScore: edge.dyad_score,
        riskFlags: edge.risk_flags,
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
          // Closer = higher compatibility
          const score = (link as PhysicsEdge).dyadScore;
          return 2 + (1 - score / 100) * 5;
        })
        .strength(0.4),
    )
    .force("charge", forceManyBody().strength(-80))
    .force("center", forceCenter(0, 0))
    .force("collide", forceCollide(0.8))
    .alphaDecay(0.02)
    .velocityDecay(0.35);

  // Simulate z-axis: add a small random impulse each tick
  // (D3 doesn't natively support z, so we integrate it manually)
  simulation.on("tick", () => {
    physicsNodes.forEach((node) => {
      // Soft spring towards z=0 (keep molecule flat-ish)
      const vz = node.z !== undefined ? -node.z * 0.02 : 0;
      node.z = (node.z ?? 0) + vz;
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
