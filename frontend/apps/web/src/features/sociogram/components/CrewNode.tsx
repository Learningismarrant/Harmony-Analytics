"use client";

import { useRef, useState } from "react";
import { useFrame } from "@react-three/fiber";
import { Html, Sphere } from "@react-three/drei";
import * as THREE from "three";
import type { PhysicsNode } from "../physics";
import { colors } from "@harmony/ui";

interface CrewNodeProps {
  node: PhysicsNode;
  isSelected: boolean;
  isCandidate?: boolean;
  onSelect: (node: PhysicsNode) => void;
}

/** Score to glow intensity — higher p_ind = brighter node */
function nodeGlowColor(pInd: number, isCandidate: boolean): THREE.Color {
  if (isCandidate) return new THREE.Color(colors.sociogram.candidate);
  if (pInd >= 75) return new THREE.Color(colors.sociogram.excellent);
  if (pInd >= 55) return new THREE.Color(colors.sociogram.good);
  return new THREE.Color(colors.sociogram.moderate);
}

export function CrewNode({ node, isSelected, isCandidate, onSelect }: CrewNodeProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  const pInd = node.data.p_ind;
  const baseColor = nodeGlowColor(pInd, isCandidate ?? false);
  const nodeRadius = 0.22 + (pInd / 100) * 0.12; // bigger = better performer

  // Pulse animation on hover/selection
  useFrame((_, delta) => {
    if (!meshRef.current) return;
    const target = hovered || isSelected ? 1.12 : 1.0;
    meshRef.current.scale.lerp(
      new THREE.Vector3(target, target, target),
      delta * 8,
    );
  });

  return (
    <group position={[node.x ?? 0, node.y ?? 0, node.z ?? 0]}>
      {/* Core sphere */}
      <mesh
        ref={meshRef}
        onClick={() => onSelect(node)}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[nodeRadius, 32, 32]} />
        <meshStandardMaterial
          color={baseColor}
          emissive={baseColor}
          emissiveIntensity={hovered || isSelected ? 0.6 : 0.25}
          roughness={0.2}
          metalness={0.7}
        />
      </mesh>

      {/* Outer glow ring (selected only) */}
      {isSelected && (
        <mesh>
          <sphereGeometry args={[nodeRadius * 1.4, 32, 32]} />
          <meshStandardMaterial
            color={baseColor}
            emissive={baseColor}
            emissiveIntensity={0.15}
            transparent
            opacity={0.12}
            side={THREE.BackSide}
          />
        </mesh>
      )}

      {/* Candidate indicator ring */}
      {isCandidate && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[nodeRadius + 0.08, 0.015, 8, 64]} />
          <meshStandardMaterial
            color={colors.sociogram.candidate}
            emissive={colors.sociogram.candidate}
            emissiveIntensity={0.8}
          />
        </mesh>
      )}

      {/* HTML label — always faces camera (drei Html) */}
      <Html
        center
        distanceFactor={12}
        position={[0, nodeRadius + 0.18, 0]}
        style={{ pointerEvents: "none" }}
      >
        <div
          style={{
            background: "rgba(7,9,15,0.80)",
            border: "1px solid rgba(26,38,52,0.8)",
            borderRadius: 6,
            padding: "2px 6px",
            fontSize: 10,
            color: "#C8D8E4",
            whiteSpace: "nowrap",
            backdropFilter: "blur(6px)",
            letterSpacing: "0.02em",
          }}
        >
          {node.data.name.split(" ")[0]}
          {isCandidate && (
            <span style={{ color: "#7850A8", marginLeft: 4 }}>★</span>
          )}
        </div>
      </Html>
    </group>
  );
}
