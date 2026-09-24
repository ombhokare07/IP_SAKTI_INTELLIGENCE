'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import type { WorkspaceSceneKey } from './PersistentWorkspaceVisual';

const MAX_POINTS = 88;
const MAX_LINES = 28;

type SceneConfig = {
  primary: string;
  secondary: string;
  accent: string;
  count: number;
  spread: number;
  core: [number, number, number];
  rhythm: number;
  planes: number;
};

const SCENES: Record<WorkspaceSceneKey, SceneConfig> = {
  dashboard: { primary: '#22d3ee', secondary: '#7c5cff', accent: '#34d399', count: 64, spread: 2.4, core: [1, 1, 1], rhythm: .055, planes: 2 },
  ask: { primary: '#67e8f9', secondary: '#8b5cf6', accent: '#34d399', count: 72, spread: 2.7, core: [.82, 1.12, .9], rhythm: .08, planes: 2 },
  patentability: { primary: '#60a5fa', secondary: '#8b5cf6', accent: '#22d3ee', count: 56, spread: 2.2, core: [1.12, .88, 1.04], rhythm: .045, planes: 4 },
  'prior-art': { primary: '#22d3ee', secondary: '#3b82f6', accent: '#7c5cff', count: 42, spread: 2.85, core: [.82, .82, .82], rhythm: .035, planes: 1 },
  'tk-risk': { primary: '#34d399', secondary: '#22d3ee', accent: '#6ee7b7', count: 68, spread: 2.25, core: [.9, 1.16, .86], rhythm: .04, planes: 3 },
  'regulation-compare': { primary: '#22d3ee', secondary: '#7c5cff', accent: '#fbbf24', count: 72, spread: 2.45, core: [1.02, 1.02, 1.02], rhythm: .032, planes: 4 },
  'document-checker': { primary: '#67e8f9', secondary: '#3b82f6', accent: '#34d399', count: 52, spread: 2.15, core: [.72, 1.2, .78], rhythm: .025, planes: 8 },
  'regulation-changes': { primary: '#7c5cff', secondary: '#22d3ee', accent: '#fbbf24', count: 54, spread: 2.75, core: [.72, .94, .72], rhythm: .07, planes: 3 },
  'compliance-journey': { primary: '#22d3ee', secondary: '#34d399', accent: '#7c5cff', count: 60, spread: 2.65, core: [.84, .84, .84], rhythm: .04, planes: 6 },
  'regulatory-alerts': { primary: '#22d3ee', secondary: '#34d399', accent: '#fbbf24', count: 34, spread: 2.9, core: [.7, .7, .7], rhythm: .02, planes: 0 },
  'knowledge-library': { primary: '#22d3ee', secondary: '#60a5fa', accent: '#34d399', count: 70, spread: 2.3, core: [.78, 1.08, .8], rhythm: .035, planes: 10 },
  reports: { primary: '#a78bfa', secondary: '#22d3ee', accent: '#34d399', count: 62, spread: 2.35, core: [.9, .9, .9], rhythm: .03, planes: 9 },
  settings: { primary: '#67e8f9', secondary: '#64748b', accent: '#34d399', count: 30, spread: 2.15, core: [.76, .76, .76], rhythm: .018, planes: 3 },
};

function pointFor(scene: WorkspaceSceneKey, index: number, spread: number): [number, number, number] {
  const t = index / MAX_POINTS;
  const angle = index * 2.399963 + scene.length * .37;
  if (scene === 'ask') return [Math.cos(angle) * spread * (1 - t * .45), (t - .5) * 4.2, Math.sin(angle) * .75];
  if (scene === 'patentability') return [((index % 4) - 1.5) * .82, Math.sin(angle) * spread * .62, Math.cos(angle) * .8];
  if (scene === 'tk-risk') {
    const radius = Math.sqrt(t) * spread;
    return [Math.cos(angle) * radius, (t - .45) * 3.4, Math.sin(angle) * radius * .36];
  }
  if (scene === 'regulation-compare') {
    const quadrant = index % 4;
    const base = quadrant * Math.PI / 2;
    return [Math.cos(base) * 1.45 + Math.cos(angle) * .55, Math.sin(base) * 1.45 + Math.sin(angle) * .55, Math.sin(angle * .7) * .65];
  }
  if (scene === 'document-checker' || scene === 'knowledge-library' || scene === 'reports') {
    return [((index % 7) - 3) * .5, (Math.floor(index / 7) % 7 - 3) * .45, Math.sin(angle) * .55];
  }
  if (scene === 'regulation-changes' || scene === 'compliance-journey') {
    return [(t - .5) * spread * 2, Math.sin(t * Math.PI * 5) * .7, (t - .5) * -2.2];
  }
  if (scene === 'regulatory-alerts' || scene === 'settings') {
    const radius = .75 + (index % 5) * .38;
    return [Math.cos(angle) * radius, Math.sin(angle) * radius, Math.sin(angle * .5) * .38];
  }
  const radius = .78 + t * spread;
  return [Math.cos(angle) * radius, Math.sin(angle * .83) * spread * .74, Math.sin(angle) * radius * .38];
}

function EvidenceField({ scene, active, compact }: { scene: WorkspaceSceneKey; active: boolean; compact: boolean }) {
  const group = useRef<THREE.Group>(null);
  const core = useRef<THREE.Mesh>(null);
  const coreMaterial = useRef<THREE.MeshBasicMaterial>(null);
  const wireMaterial = useRef<THREE.MeshBasicMaterial>(null);
  const pointMaterial = useRef<THREE.PointsMaterial>(null);
  const lineMaterial = useRef<THREE.LineBasicMaterial>(null);
  const pointsGeometry = useRef<THREE.BufferGeometry>(null);
  const linesGeometry = useRef<THREE.BufferGeometry>(null);
  const planes = useRef<THREE.InstancedMesh>(null);
  const { invalidate } = useThree();
  const pointer = useRef({ x: 0, y: 0 });
  const currentPoints = useMemo(() => new Float32Array(MAX_POINTS * 3), []);
  const targetPoints = useMemo(() => new Float32Array(MAX_POINTS * 3), []);
  const linePositions = useMemo(() => new Float32Array(MAX_LINES * 2 * 3), []);
  const config = SCENES[scene];
  const targetPrimary = useMemo(() => new THREE.Color(config.primary), [config.primary]);
  const targetSecondary = useMemo(() => new THREE.Color(config.secondary), [config.secondary]);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useEffect(() => {
    const move = (event: PointerEvent) => {
      pointer.current.x = event.clientX / window.innerWidth - .5;
      pointer.current.y = event.clientY / window.innerHeight - .5;
    };
    window.addEventListener('pointermove', move, { passive: true });
    return () => window.removeEventListener('pointermove', move);
  }, []);

  useEffect(() => {
    for (let index = 0; index < MAX_POINTS; index += 1) {
      const [x, y, z] = pointFor(scene, index, config.spread);
      targetPoints[index * 3] = x;
      targetPoints[index * 3 + 1] = y;
      targetPoints[index * 3 + 2] = z;
    }
    pointsGeometry.current?.setDrawRange(0, compact ? Math.min(config.count, 46) : config.count);
    if (planes.current) {
      planes.current.count = compact ? Math.min(config.planes, 5) : config.planes;
      for (let index = 0; index < planes.current.count; index += 1) {
        dummy.position.set(1.15 + (index % 3) * .34, -1.15 + Math.floor(index / 3) * .31, -.65 - index * .035);
        dummy.rotation.set(-.15, -.42, -.08 + index * .025);
        dummy.scale.set(.56, .34, 1);
        dummy.updateMatrix();
        planes.current.setMatrixAt(index, dummy.matrix);
      }
      planes.current.instanceMatrix.needsUpdate = true;
    }
    invalidate();
  }, [compact, config, dummy, invalidate, scene, targetPoints]);

  useFrame((state, delta) => {
    if (!active || !group.current) return;
    const smoothing = 1 - Math.exp(-delta * 3.4);
    for (let index = 0; index < currentPoints.length; index += 1) {
      currentPoints[index] = THREE.MathUtils.lerp(currentPoints[index], targetPoints[index], smoothing);
    }
    const points = pointsGeometry.current?.attributes.position as THREE.BufferAttribute | undefined;
    if (points) points.needsUpdate = true;
    for (let index = 0; index < MAX_LINES; index += 1) {
      const pointIndex = (index * 3 % Math.max(1, config.count)) * 3;
      const base = index * 6;
      linePositions[base] = currentPoints[pointIndex];
      linePositions[base + 1] = currentPoints[pointIndex + 1];
      linePositions[base + 2] = currentPoints[pointIndex + 2];
      linePositions[base + 3] = currentPoints[pointIndex] * .16;
      linePositions[base + 4] = currentPoints[pointIndex + 1] * .16;
      linePositions[base + 5] = currentPoints[pointIndex + 2] * .16;
    }
    const lines = linesGeometry.current?.attributes.position as THREE.BufferAttribute | undefined;
    if (lines) lines.needsUpdate = true;
    coreMaterial.current?.color.lerp(targetPrimary, smoothing);
    wireMaterial.current?.color.lerp(targetSecondary, smoothing);
    pointMaterial.current?.color.lerp(targetPrimary, smoothing);
    lineMaterial.current?.color.lerp(targetSecondary, smoothing);
    if (core.current) {
      core.current.scale.x = THREE.MathUtils.lerp(core.current.scale.x, config.core[0], smoothing);
      core.current.scale.y = THREE.MathUtils.lerp(core.current.scale.y, config.core[1], smoothing);
      core.current.scale.z = THREE.MathUtils.lerp(core.current.scale.z, config.core[2], smoothing);
    }
    group.current.rotation.y += delta * config.rhythm;
    group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, pointer.current.y * .08, smoothing * .45);
    group.current.rotation.z = THREE.MathUtils.lerp(group.current.rotation.z, pointer.current.x * -.06, smoothing * .45);
    group.current.position.x = THREE.MathUtils.lerp(group.current.position.x, .65 + pointer.current.x * .13, smoothing * .4);
    group.current.position.y = THREE.MathUtils.lerp(group.current.position.y, pointer.current.y * -.1, smoothing * .4);
    const pulse = 1 + Math.sin(state.clock.elapsedTime * .42) * .018;
    group.current.scale.setScalar(pulse);
  });

  return <group ref={group} position={[.65, 0, 0]}>
    <mesh ref={core}>
      <icosahedronGeometry args={[.86, 2]} />
      <meshBasicMaterial ref={coreMaterial} color={config.primary} transparent opacity={.13} depthWrite={false} />
    </mesh>
    <mesh scale={1.035} rotation={[.25, .1, 0]}>
      <icosahedronGeometry args={[.86, 1]} />
      <meshBasicMaterial ref={wireMaterial} color={config.secondary} transparent opacity={.34} wireframe depthWrite={false} />
    </mesh>
    <mesh rotation={[Math.PI / 2.3, .2, 0]}>
      <torusGeometry args={[1.34, .008, 3, 72]} />
      <meshBasicMaterial color={config.primary} transparent opacity={.26} depthWrite={false} />
    </mesh>
    <mesh rotation={[Math.PI / 1.7, .7, .35]}>
      <torusGeometry args={[1.72, .006, 3, 72]} />
      <meshBasicMaterial color={config.secondary} transparent opacity={.2} depthWrite={false} />
    </mesh>
    <lineSegments>
      <bufferGeometry ref={linesGeometry}>
        <bufferAttribute attach="attributes-position" args={[linePositions, 3]} />
      </bufferGeometry>
      <lineBasicMaterial ref={lineMaterial} color={config.secondary} transparent opacity={.105} depthWrite={false} />
    </lineSegments>
    <points>
      <bufferGeometry ref={pointsGeometry}>
        <bufferAttribute attach="attributes-position" args={[currentPoints, 3]} />
      </bufferGeometry>
      <pointsMaterial ref={pointMaterial} color={config.primary} size={compact ? .025 : .03} transparent opacity={.72} sizeAttenuation depthWrite={false} />
    </points>
    <instancedMesh ref={planes} args={[undefined, undefined, 10]}>
      <planeGeometry args={[1, 1]} />
      <meshBasicMaterial color={config.accent} transparent opacity={.055} wireframe depthWrite={false} />
    </instancedMesh>
  </group>;
}

export default function PersistentWorkspaceScene({ scene, compact }: { scene: WorkspaceSceneKey; compact: boolean }) {
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    const update = () => setVisible(document.visibilityState === 'visible');
    update();
    document.addEventListener('visibilitychange', update);
    return () => document.removeEventListener('visibilitychange', update);
  }, []);

  return <Canvas
    dpr={compact ? [0.8, 1.05] : [1, 1.3]}
    camera={{ position: [0, 0, 5.4], fov: 46 }}
    frameloop={visible ? 'always' : 'demand'}
    gl={{ alpha: true, antialias: !compact, powerPreference: 'low-power' }}
  >
    <ambientLight intensity={.45} />
    <directionalLight position={[3, 4, 5]} intensity={.55} color="#bff7ff" />
    <EvidenceField scene={scene} active={visible} compact={compact} />
  </Canvas>;
}
