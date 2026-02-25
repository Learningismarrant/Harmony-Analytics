/**
 * sociogram physics — unit tests
 *
 * buildSimulation() is a pure function with no DOM/React dependencies,
 * so we can test it without jsdom.
 */

import { buildSimulation, pauseWhenConverged } from "./physics";
import type { SociogramNode, SociogramEdge } from "@harmony/types";

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makeNode(id: number): SociogramNode {
  return {
    crew_profile_id: id,
    name: `Crew ${id}`,
    p_ind: 70,
    f_team: 0.7,
    days_aboard: 30,
    position: "Deckhand",
    avatar_url: null,
  };
}

function makeEdge(sourceId: number, targetId: number, score = 75): SociogramEdge {
  return {
    source_id: sourceId,
    target_id: targetId,
    dyad_score: score,
    agreeableness_compatibility: score,
    conscientiousness_compatibility: score,
    es_compatibility: score,
    risk_flags: [],
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("buildSimulation", () => {
  it("returns empty arrays for no nodes or edges", () => {
    const { physicsNodes, physicsEdges } = buildSimulation([], []);
    expect(physicsNodes).toHaveLength(0);
    expect(physicsEdges).toHaveLength(0);
  });

  it("creates one PhysicsNode per SociogramNode with x, y, z, vz fields", () => {
    const nodes = [makeNode(1), makeNode(2), makeNode(3)];
    const { physicsNodes } = buildSimulation(nodes, []);
    expect(physicsNodes).toHaveLength(3);
    for (const n of physicsNodes) {
      expect(typeof n.x).toBe("number");
      expect(typeof n.y).toBe("number");
      expect(typeof n.z).toBe("number");
      expect(typeof n.vz).toBe("number");
    }
  });

  it("builds physics edges that reference PhysicsNode objects (not raw ids)", () => {
    const nodes = [makeNode(10), makeNode(20)];
    const edges = [makeEdge(10, 20, 80)];
    const { physicsNodes, physicsEdges } = buildSimulation(nodes, edges);
    expect(physicsEdges).toHaveLength(1);
    // source/target must be the actual PhysicsNode objects from physicsNodes
    expect(physicsEdges[0].source).toBe(physicsNodes.find((n) => n.id === 10));
    expect(physicsEdges[0].target).toBe(physicsNodes.find((n) => n.id === 20));
  });

  it("drops edges whose source or target id does not match any node", () => {
    const nodes = [makeNode(1)];
    const edges = [makeEdge(1, 999)]; // target 999 doesn't exist
    const { physicsEdges } = buildSimulation(nodes, edges);
    expect(physicsEdges).toHaveLength(0);
  });

  describe("with candidateNode", () => {
    it("adds the candidate as an extra node with isCandidate=true", () => {
      const nodes = [makeNode(1), makeNode(2)];
      const candidate = makeNode(99);
      const { physicsNodes } = buildSimulation(nodes, [], candidate);
      expect(physicsNodes).toHaveLength(3);
      const cNode = physicsNodes.find((n) => n.id === 99);
      expect(cNode?.isCandidate).toBe(true);
    });

    it("uses provided candidateEdges (marks them isCandidate=true)", () => {
      const nodes = [makeNode(1), makeNode(2)];
      const candidate = makeNode(99);
      const candidateEdges = [makeEdge(99, 1, 85), makeEdge(99, 2, 60)];
      const { physicsEdges } = buildSimulation(nodes, [], candidate, candidateEdges);
      const candEdges = physicsEdges.filter((e) => e.isCandidate);
      expect(candEdges).toHaveLength(2);
    });

    it("generates fallback edges to all nodes when candidateEdges is empty", () => {
      const nodes = [makeNode(1), makeNode(2), makeNode(3)];
      const candidate = makeNode(99);
      const { physicsEdges } = buildSimulation(nodes, [], candidate, []);
      const candEdges = physicsEdges.filter((e) => e.isCandidate);
      // One fallback edge per existing node
      expect(candEdges).toHaveLength(nodes.length);
      // Fallback dyad score is 50
      expect(candEdges.every((e) => e.dyadScore === 50)).toBe(true);
    });
  });

  it("simulation object has a tick method (D3 Simulation)", () => {
    const nodes = [makeNode(1), makeNode(2)];
    const { simulation } = buildSimulation(nodes, [makeEdge(1, 2)]);
    expect(typeof simulation.tick).toBe("function");
    expect(typeof simulation.stop).toBe("function");
  });
});

describe("pauseWhenConverged", () => {
  it("returns a cleanup function", () => {
    const { simulation } = buildSimulation([makeNode(1)], []);
    const cleanup = pauseWhenConverged(simulation);
    expect(typeof cleanup).toBe("function");
    // Cleanup should not throw
    expect(() => cleanup()).not.toThrow();
  });
});
