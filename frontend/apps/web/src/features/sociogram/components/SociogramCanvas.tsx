"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import * as THREE from "three";
import { CrewNode } from "./CrewNode";
import { DyadEdge } from "./DyadEdge";
import { NodeInfoPanel } from "./NodeInfoPanel";
import { SimulationOverlay } from "./SimulationOverlay";
import {
  buildSimulation,
  type PhysicsNode,
  type PhysicsEdge,
} from "../physics";
import type { SociogramOut, SimulationPreviewOut } from "@harmony/types";

// ── Scene graph component ────────────────────────────────────────────────────

interface MoleculeSceneProps {
  physicsNodes: PhysicsNode[];
  physicsEdges: PhysicsEdge[];
  selectedNode: PhysicsNode | null;
  onSelectNode: (node: PhysicsNode | null) => void;
  tick: number; // increment to force re-render during physics
}

function MoleculeScene({
  physicsNodes,
  physicsEdges,
  selectedNode,
  onSelectNode,
  tick: _tick,
}: MoleculeSceneProps) {
  return (
    <>
      {/* Ambient + directional light */}
      <ambientLight intensity={0.15} color="#1E2733" />
      <directionalLight position={[10, 15, 10]} intensity={0.8} color="#E8EFF7" />
      <pointLight position={[-8, -8, -8]} intensity={0.4} color="#0EA5E9" />

      {/* Stars background */}
      <Stars
        radius={60}
        depth={30}
        count={800}
        factor={2}
        saturation={0}
        fade
        speed={0.5}
      />

      {/* Edges — rendered before nodes for correct transparency */}
      {physicsEdges.map((edge) => (
        <DyadEdge
          key={`edge-${edge.source.id}-${edge.target.id}`}
          edge={edge}
          opacity={edge.isCandidate ? 0.55 : 1}
        />
      ))}

      {/* Nodes */}
      {physicsNodes.map((node) => (
        <CrewNode
          key={`node-${node.id}`}
          node={node}
          isSelected={selectedNode?.id === node.id}
          isCandidate={node.isCandidate}
          onSelect={(n) => onSelectNode(selectedNode?.id === n.id ? null : n)}
        />
      ))}
    </>
  );
}

// ── Physics tick updater ─────────────────────────────────────────────────────

function PhysicsTicker({ onTick }: { onTick: () => void }) {
  useFrame(() => {
    onTick();
  });
  return null;
}

// ── Main exported component ──────────────────────────────────────────────────

interface SociogramCanvasProps {
  sociogram: SociogramOut;
  simulationPreview?: SimulationPreviewOut | null;
  onSimulationRequest?: (crewProfileId: number) => void;
  onHireCandidate?: () => void;
  onCancelSimulation?: () => void;
  loadingSimulation?: boolean;
  className?: string;
}

export function SociogramCanvas({
  sociogram,
  simulationPreview,
  onSimulationRequest,
  onHireCandidate,
  onCancelSimulation,
  loadingSimulation,
  className = "",
}: SociogramCanvasProps) {
  const [physicsNodes, setPhysicsNodes] = useState<PhysicsNode[]>([]);
  const [physicsEdges, setPhysicsEdges] = useState<PhysicsEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<PhysicsNode | null>(null);
  const [tick, setTick] = useState(0);
  const [converged, setConverged] = useState(false);

  const simulationRef = useRef<ReturnType<typeof buildSimulation>["simulation"] | null>(null);

  // ── Build / rebuild simulation when sociogram or preview changes ─────────────
  useEffect(() => {
    simulationRef.current?.stop();
    setConverged(false);
    setSelectedNode(null);

    // Inject candidate node when a simulation preview is active
    let candidateNode = undefined;
    let candidateEdges = undefined;
    if (simulationPreview) {
      candidateNode = {
        crew_profile_id: simulationPreview.candidate_id,
        name: simulationPreview.candidate_name,
        avatar_url: null as null,
        position: "Candidate",
        psychometric_completeness: 1.0,
        p_ind: 60, // visual default for node size/color
      };
      candidateEdges = simulationPreview.new_edges;
    }

    const { simulation, physicsNodes: pNodes, physicsEdges: pEdges } =
      buildSimulation(sociogram.nodes, sociogram.edges, candidateNode, candidateEdges);

    simulationRef.current = simulation;
    setPhysicsNodes(pNodes);
    setPhysicsEdges(pEdges);

    simulation.on("end", () => {
      setConverged(true);
      simulation.stop();
    });

    return () => {
      simulation.stop();
    };
  }, [sociogram, simulationPreview]);

  // Force re-render while physics is running
  const handleTick = useCallback(() => {
    if (!converged) {
      simulationRef.current?.tick();
      setTick((t) => t + 1);
    }
  }, [converged]);

  const handleSimulate = useCallback(
    (node: PhysicsNode) => {
      onSimulationRequest?.(node.id);
    },
    [onSimulationRequest],
  );

  return (
    <div className={`relative ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 18], fov: 55, near: 0.1, far: 200 }}
        gl={{ antialias: true, alpha: false, toneMapping: THREE.ACESFilmicToneMapping }}
        style={{ background: "radial-gradient(ellipse at center, #0A1520 0%, #07090F 75%)" }}
      >
        <PhysicsTicker onTick={handleTick} />
        <MoleculeScene
          physicsNodes={physicsNodes}
          physicsEdges={physicsEdges}
          selectedNode={selectedNode}
          onSelectNode={setSelectedNode}
          tick={tick}
        />
        <OrbitControls
          enableDamping
          dampingFactor={0.08}
          minDistance={4}
          maxDistance={40}
          rotateSpeed={0.5}
          zoomSpeed={0.8}
        />
      </Canvas>

      {/* HUD — team score */}
      <div className="absolute top-4 left-4 pointer-events-none">
        <div className="card py-2 px-3 inline-block">
          <p className="text-xs text-muted">F_team score</p>
          <p className="text-xl font-semibold text-brand-primary">
            {Math.round(sociogram.f_team_global)}
            <span className="text-xs text-muted font-normal ml-1">/ 100</span>
          </p>
          <p className="text-xs text-muted mt-0.5">
            {sociogram.nodes.length} crew members
            {simulationPreview && <span className="text-brand-secondary ml-1">+1 candidate</span>}
          </p>
        </div>
      </div>

      {/* Physics status */}
      {!converged && (
        <div className="absolute bottom-4 left-4 pointer-events-none">
          <div className="badge badge-info animate-pulse">
            ◌ Calculating positions…
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 right-4 pointer-events-none">
        <div className="card py-2 px-3 text-xs space-y-1">
          <p className="text-muted text-xs mb-1.5 font-medium">Dyad compatibility</p>
          {[
            { label: "≥80 — Excellent", color: "bg-green-500" },
            { label: "65–80 — Good", color: "bg-lime-500" },
            { label: "45–65 — Moderate", color: "bg-amber-500" },
            { label: "<45 — Weak", color: "bg-red-500" },
          ].map(({ label, color }) => (
            <div key={label} className="flex items-center gap-1.5">
              <div className={`w-2 h-2 rounded-full ${color}`} />
              <span className="text-muted">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Node info panel */}
      {selectedNode && (
        <NodeInfoPanel
          node={selectedNode}
          edges={physicsEdges}
          onClose={() => setSelectedNode(null)}
          onSimulate={onSimulationRequest ? handleSimulate : undefined}
          isCandidate={selectedNode.isCandidate}
        />
      )}

      {/* Simulation result overlay */}
      {simulationPreview && (
        <SimulationOverlay
          preview={simulationPreview}
          onAccept={onHireCandidate ?? (() => {})}
          onCancel={onCancelSimulation ?? (() => {})}
          loading={loadingSimulation}
        />
      )}
    </div>
  );
}
