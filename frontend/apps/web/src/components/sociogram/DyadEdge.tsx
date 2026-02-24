"use client";

import { useMemo } from "react";
import * as THREE from "three";
import type { PhysicsEdge } from "@/lib/sociogram-physics";
import { dyadScoreToColor, dyadScoreToThickness } from "@harmony/ui";

interface DyadEdgeProps {
  edge: PhysicsEdge;
  opacity?: number;
}

/**
 * Renders a single dyad edge as a tapered cylinder between two nodes.
 *
 * Color:     green → yellow → red based on dyad_score
 * Thickness: proportional to dyad_score
 * Opacity:   dimmed when simulation mode is active
 */
export function DyadEdge({ edge, opacity = 1 }: DyadEdgeProps) {
  const { source, target, dyadScore } = edge;

  const { position, rotation, length } = useMemo(() => {
    const start = new THREE.Vector3(source.x ?? 0, source.y ?? 0, source.z ?? 0);
    const end = new THREE.Vector3(target.x ?? 0, target.y ?? 0, target.z ?? 0);

    const direction = end.clone().sub(start);
    const len = direction.length();
    const mid = start.clone().add(end).multiplyScalar(0.5);

    // Align cylinder (default Y-axis) to the direction vector
    const quaternion = new THREE.Quaternion();
    quaternion.setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      direction.normalize(),
    );
    const euler = new THREE.Euler().setFromQuaternion(quaternion);

    return {
      position: [mid.x, mid.y, mid.z] as [number, number, number],
      rotation: [euler.x, euler.y, euler.z] as [number, number, number],
      length: len,
    };
  }, [source.x, source.y, source.z, target.x, target.y, target.z]);

  const color = new THREE.Color().setHex(dyadScoreToColor(dyadScore));
  const thickness = dyadScoreToThickness(dyadScore);
  const hasRisk = edge.riskFlags.length > 0;

  return (
    <mesh position={position} rotation={rotation}>
      <cylinderGeometry args={[thickness, thickness, length, 8]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={hasRisk ? 0.5 : 0.2}
        transparent
        opacity={opacity * (hasRisk ? 0.9 : 0.65)}
        roughness={0.6}
        metalness={0.2}
      />
    </mesh>
  );
}
