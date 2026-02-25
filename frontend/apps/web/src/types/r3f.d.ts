/**
 * R3F v9 + React 19 — JSX type augmentation
 *
 * @react-three/fiber v9 no longer automatically merges ThreeElements into
 * React's JSX namespace when using the new JSX transform (jsxImportSource).
 * This file restores the merge so Three.js primitives (ambientLight,
 * directionalLight, mesh, etc.) are recognized as valid JSX elements.
 */
import type { ThreeElements } from "@react-three/fiber";

declare module "react" {
  namespace JSX {
    interface IntrinsicElements extends ThreeElements {}
  }
}
