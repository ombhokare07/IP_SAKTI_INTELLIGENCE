'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { getSceneSignal } from '@/services/scene-signals.mjs';
import type { WorkspaceSceneKey } from './PersistentWorkspaceVisual';

const MAX_POINTS = 88;
const MAX_LINES = 28;
const MAX_NODES = 15;
const MAX_PLANES = 10;

type SceneConfig = {
  primary: string; secondary: string; accent: string; count: number; spread: number;
  core: [number, number, number]; rhythm: number; planes: number;
  position: [number, number, number]; camera: [number, number, number];
  ringTilt: [number, number, number]; conceptualNodes: number;
};

const SCENES: Record<WorkspaceSceneKey, SceneConfig> = {
  dashboard: { primary: '#22d3ee', secondary: '#7c5cff', accent: '#34d399', count: 76, spread: 2.6, core: [1.08, 1.08, 1.08], rhythm: .07, planes: 3, position: [.82, -.04, 0], camera: [0, 0, 5.25], ringTilt: [.3, .62, 1.05], conceptualNodes: 6 },
  ask: { primary: '#67e8f9', secondary: '#8b5cf6', accent: '#34d399', count: 72, spread: 2.7, core: [.82, 1.12, .9], rhythm: .08, planes: 2, position: [.62, 0, .05], camera: [0, 0, 5.25], ringTilt: [.5, .9, 1.28], conceptualNodes: 0 },
  patentability: { primary: '#60a5fa', secondary: '#8b5cf6', accent: '#22d3ee', count: 56, spread: 2.25, core: [1.12, .88, 1.04], rhythm: .055, planes: 4, position: [.72, -.03, 0], camera: [.08, 0, 5.35], ringTilt: [.18, .74, 1.42], conceptualNodes: 0 },
  'prior-art': { primary: '#22d3ee', secondary: '#3b82f6', accent: '#7c5cff', count: 48, spread: 2.95, core: [.82, .82, .82], rhythm: .05, planes: 1, position: [.64, 0, 0], camera: [0, 0, 5.55], ringTilt: [.72, 1.05, .22], conceptualNodes: 0 },
  'tk-risk': { primary: '#34d399', secondary: '#22d3ee', accent: '#6ee7b7', count: 68, spread: 2.35, core: [.9, 1.16, .86], rhythm: .048, planes: 6, position: [.68, -.08, 0], camera: [0, 0, 5.35], ringTilt: [.45, 1.22, .7], conceptualNodes: 0 },
  'regulation-compare': { primary: '#22d3ee', secondary: '#7c5cff', accent: '#fbbf24', count: 72, spread: 2.5, core: [1.02, 1.02, 1.02], rhythm: .045, planes: 4, position: [.68, 0, 0], camera: [0, 0, 5.45], ringTilt: [.9, .4, 1.3], conceptualNodes: 4 },
  'document-checker': { primary: '#67e8f9', secondary: '#3b82f6', accent: '#34d399', count: 52, spread: 2.2, core: [.72, 1.2, .78], rhythm: .04, planes: 8, position: [.75, -.04, 0], camera: [0, 0, 5.3], ringTilt: [.25, 1.15, .52], conceptualNodes: 0 },
  'regulation-changes': { primary: '#7c5cff', secondary: '#22d3ee', accent: '#fbbf24', count: 54, spread: 2.8, core: [.72, .94, .72], rhythm: .065, planes: 3, position: [.5, .02, 0], camera: [0, 0, 5.6], ringTilt: [.65, .26, 1.12], conceptualNodes: 0 },
  'compliance-journey': { primary: '#22d3ee', secondary: '#34d399', accent: '#7c5cff', count: 60, spread: 2.75, core: [.84, .84, .84], rhythm: .05, planes: 6, position: [.5, .02, 0], camera: [0, 0, 5.6], ringTilt: [.35, 1.04, .88], conceptualNodes: 7 },
  'regulatory-alerts': { primary: '#22d3ee', secondary: '#34d399', accent: '#fbbf24', count: 34, spread: 3, core: [.7, .7, .7], rhythm: .035, planes: 0, position: [.64, 0, 0], camera: [0, 0, 5.5], ringTilt: [1.1, .5, .15], conceptualNodes: 0 },
  'knowledge-library': { primary: '#22d3ee', secondary: '#60a5fa', accent: '#34d399', count: 70, spread: 2.4, core: [.78, 1.08, .8], rhythm: .045, planes: 10, position: [.72, -.05, 0], camera: [0, 0, 5.4], ringTilt: [.4, .84, 1.2], conceptualNodes: 0 },
  reports: { primary: '#a78bfa', secondary: '#22d3ee', accent: '#34d399', count: 62, spread: 2.4, core: [.9, .9, .9], rhythm: .045, planes: 9, position: [.7, -.04, 0], camera: [0, 0, 5.4], ringTilt: [.82, .34, 1.06], conceptualNodes: 0 },
  settings: { primary: '#67e8f9', secondary: '#64748b', accent: '#34d399', count: 30, spread: 2.2, core: [.76, .76, .76], rhythm: .028, planes: 3, position: [.65, 0, 0], camera: [0, 0, 5.3], ringTilt: [.55, .95, .2], conceptualNodes: 0 },
};

function pointFor(scene: WorkspaceSceneKey, index: number, count: number, spread: number, target: Float32Array) {
  const t = count <= 1 ? 0 : Math.min(index, count - 1) / (count - 1);
  const angle = index * 2.399963 + scene.length * .37;
  const offset = index * 3;
  let x = 0; let y = 0; let z = 0;
  if (scene === 'ask') { x = Math.cos(angle) * spread * (1 - t * .45); y = (t - .5) * 4.4; z = Math.sin(angle) * .8; }
  else if (scene === 'patentability') { x = ((index % 4) - 1.5) * .84; y = (t - .5) * spread * 1.8; z = Math.cos(angle) * .85; }
  else if (scene === 'tk-risk') { const radius = Math.sqrt(t) * spread; x = Math.cos(angle) * radius; y = (t - .45) * 3.5; z = Math.sin(angle) * radius * .38; }
  else if (scene === 'regulation-compare') { const base = (index % 4) * Math.PI / 2; x = Math.cos(base) * 1.48 + Math.cos(angle) * .58; y = Math.sin(base) * 1.48 + Math.sin(angle) * .58; z = Math.sin(angle * .7) * .68; }
  else if (scene === 'document-checker' || scene === 'knowledge-library' || scene === 'reports') { x = ((index % 7) - 3) * .52; y = (Math.floor(index / 7) % 8 - 3.5) * .45; z = Math.sin(angle) * .58; }
  else if (scene === 'regulation-changes' || scene === 'compliance-journey') { x = (t - .5) * spread * 2; y = Math.sin(t * Math.PI * 5) * .72; z = (t - .5) * -2.3; }
  else if (scene === 'regulatory-alerts' || scene === 'settings') { const radius = .76 + (index % 5) * .4; x = Math.cos(angle) * radius; y = Math.sin(angle) * radius; z = Math.sin(angle * .5) * .4; }
  else { const radius = .78 + t * spread; x = Math.cos(angle) * radius; y = Math.sin(angle * .83) * spread * .76; z = Math.sin(angle) * radius * .4; }
  target[offset] = x; target[offset + 1] = y; target[offset + 2] = z;
}

function EvidenceField({ scene, active, compact }: { scene: WorkspaceSceneKey; active: boolean; compact: boolean }) {
  const group = useRef<THREE.Group>(null);
  const core = useRef<THREE.Mesh>(null);
  const innerCore = useRef<THREE.Mesh>(null);
  const ringA = useRef<THREE.Mesh>(null); const ringB = useRef<THREE.Mesh>(null); const ringC = useRef<THREE.Mesh>(null);
  const coreMaterial = useRef<THREE.MeshBasicMaterial>(null); const innerMaterial = useRef<THREE.MeshStandardMaterial>(null); const wireMaterial = useRef<THREE.MeshBasicMaterial>(null);
  const ringMaterialA = useRef<THREE.MeshBasicMaterial>(null); const ringMaterialB = useRef<THREE.MeshBasicMaterial>(null); const ringMaterialC = useRef<THREE.MeshBasicMaterial>(null);
  const pointMaterial = useRef<THREE.PointsMaterial>(null); const lineMaterial = useRef<THREE.LineBasicMaterial>(null);
  const planeMaterial = useRef<THREE.MeshBasicMaterial>(null);
  const pointsGeometry = useRef<THREE.BufferGeometry>(null); const linesGeometry = useRef<THREE.BufferGeometry>(null);
  const nodes = useRef<THREE.InstancedMesh>(null); const planes = useRef<THREE.InstancedMesh>(null);
  const activityA = useRef<THREE.Mesh>(null); const activityB = useRef<THREE.Mesh>(null); const keyLight = useRef<THREE.DirectionalLight>(null);
  const { camera, invalidate } = useThree();
  const pointer = useRef({ x: 0, y: 0 });
  const currentPoints = useMemo(() => new Float32Array(MAX_POINTS * 3), []);
  const displayPoints = useMemo(() => new Float32Array(MAX_POINTS * 3), []);
  const targetPoints = useMemo(() => new Float32Array(MAX_POINTS * 3), []);
  const linePositions = useMemo(() => new Float32Array(MAX_LINES * 2 * 3), []);
  const phases = useMemo(() => Float32Array.from({ length: MAX_POINTS }, (_, index) => index * 1.713 + .4), []);
  const speeds = useMemo(() => Float32Array.from({ length: MAX_POINTS }, (_, index) => .32 + (index % 9) * .027), []);
  const amplitudes = useMemo(() => Float32Array.from({ length: MAX_POINTS }, (_, index) => .012 + (index % 7) * .003), []);
  const config = SCENES[scene];
  const targetPrimary = useMemo(() => new THREE.Color(config.primary), [config.primary]);
  const targetSecondary = useMemo(() => new THREE.Color(config.secondary), [config.secondary]);
  const targetAccent = useMemo(() => new THREE.Color(config.accent), [config.accent]);
  const errorColor = useMemo(() => new THREE.Color('#fb7185'), []);
  const warningColor = useMemo(() => new THREE.Color('#fbbf24'), []);
  const readyColor = useMemo(() => new THREE.Color('#34d399'), []);
  const neutralColor = useMemo(() => new THREE.Color('#496078'), []);
  const dummy = useMemo(() => new THREE.Object3D(), []); const lookTarget = useMemo(() => new THREE.Vector3(), []);

  useEffect(() => {
    const move = (event: PointerEvent) => { pointer.current.x = event.clientX / window.innerWidth - .5; pointer.current.y = event.clientY / window.innerHeight - .5; };
    window.addEventListener('pointermove', move, { passive: true });
    return () => window.removeEventListener('pointermove', move);
  }, []);

  useEffect(() => {
    for (let index = 0; index < MAX_POINTS; index += 1) pointFor(scene, index, config.count, config.spread, targetPoints);
    pointsGeometry.current?.setDrawRange(0, compact ? Math.min(config.count, 46) : config.count);
    linesGeometry.current?.setDrawRange(0, Math.min(MAX_LINES, Math.max(10, Math.floor(config.count * .38))) * 2);
    invalidate();
  }, [compact, config, invalidate, scene, targetPoints]);

  useFrame((state, delta) => {
    if (!active || !group.current) return;
    const signal = getSceneSignal(); const time = state.clock.elapsedTime;
    const smoothing = 1 - Math.exp(-delta * 4.8); const motionStrength = compact ? .55 : 1;
    const processing = signal.phase === 'submitting' || signal.phase === 'processing';
    const hoverEnergy = signal.hover ? .32 : 0;
    const phaseEnergy = processing ? 1 : signal.phase === 'error' ? .7 : signal.phase === 'success' ? .55 : .2;
    const pulseAge = signal.pulseAt ? (performance.now() - signal.pulseAt) / 1000 : 99;
    const pulse = pulseAge < 1.25 ? Math.sin(Math.min(1, pulseAge / 1.25) * Math.PI) : 0;

    for (let index = 0; index < MAX_POINTS; index += 1) {
      const base = index * 3;
      currentPoints[base] = THREE.MathUtils.lerp(currentPoints[base], targetPoints[base], smoothing);
      currentPoints[base + 1] = THREE.MathUtils.lerp(currentPoints[base + 1], targetPoints[base + 1], smoothing);
      currentPoints[base + 2] = THREE.MathUtils.lerp(currentPoints[base + 2], targetPoints[base + 2], smoothing);
      const drift = Math.sin(time * speeds[index] + phases[index]) * amplitudes[index] * motionStrength;
      const routePulse = (scene === 'ask' || scene === 'prior-art') ? 1 + pulse * .09 : 1;
      const convergence = (processing ? .9 : 1) * routePulse;
      displayPoints[base] = currentPoints[base] * convergence + drift;
      displayPoints[base + 1] = currentPoints[base + 1] * convergence + Math.cos(time * speeds[index] * .8 + phases[index]) * amplitudes[index] * motionStrength;
      displayPoints[base + 2] = currentPoints[base + 2] + drift * 1.8;
    }
    const pointAttribute = pointsGeometry.current?.attributes.position as THREE.BufferAttribute | undefined; if (pointAttribute) pointAttribute.needsUpdate = true;
    const densityCount = signal.density === undefined ? config.count : Math.min(config.count, 18 + signal.density);
    pointsGeometry.current?.setDrawRange(0, compact ? Math.min(densityCount, 46) : densityCount);

    const lineCount = Math.min(MAX_LINES, Math.max(10, Math.floor(config.count * .38)));
    for (let index = 0; index < MAX_LINES; index += 1) {
      const from = ((index * 3) % config.count) * 3; const to = ((index * 7 + 5) % config.count) * 3; const base = index * 6;
      linePositions[base] = displayPoints[from]; linePositions[base + 1] = displayPoints[from + 1]; linePositions[base + 2] = displayPoints[from + 2];
      linePositions[base + 3] = displayPoints[to]; linePositions[base + 4] = displayPoints[to + 1]; linePositions[base + 5] = displayPoints[to + 2];
    }
    const lineAttribute = linesGeometry.current?.attributes.position as THREE.BufferAttribute | undefined; if (lineAttribute) lineAttribute.needsUpdate = true;

    coreMaterial.current?.color.lerp(signal.phase === 'error' ? errorColor : targetPrimary, smoothing);
    wireMaterial.current?.color.lerp(targetSecondary, smoothing); pointMaterial.current?.color.lerp(targetPrimary, smoothing);
    lineMaterial.current?.color.lerp(signal.phase === 'partial' ? targetAccent : targetSecondary, smoothing);
    if (innerMaterial.current) { innerMaterial.current.color.lerp(targetPrimary, smoothing); innerMaterial.current.emissive.lerp(signal.phase === 'error' ? errorColor : targetSecondary, smoothing); innerMaterial.current.emissiveIntensity = .36 + phaseEnergy * .22 + pulse * .5; }
    const liveAccent = signal.riskTone === 'high' || signal.phase === 'error' || signal.providerTone === 'unavailable'
      ? errorColor
      : signal.riskTone === 'medium' || signal.providerTone === 'partial'
        ? warningColor
        : signal.riskTone === 'low' || signal.providerTone === 'ready'
          ? readyColor
          : targetAccent;
    ringMaterialA.current?.color.lerp(targetPrimary, smoothing); ringMaterialB.current?.color.lerp(targetSecondary, smoothing); ringMaterialC.current?.color.lerp(liveAccent, smoothing);
    if (ringMaterialA.current) ringMaterialA.current.opacity = .36 + hoverEnergy;
    if (ringMaterialB.current) ringMaterialB.current.opacity = .28 + hoverEnergy * .55;

    const breath = 1 + Math.sin(time * 1.8) * .035 + pulse * .11;
    if (core.current) { core.current.scale.x = THREE.MathUtils.lerp(core.current.scale.x, config.core[0] * breath, smoothing); core.current.scale.y = THREE.MathUtils.lerp(core.current.scale.y, config.core[1] * breath, smoothing); core.current.scale.z = THREE.MathUtils.lerp(core.current.scale.z, config.core[2] * breath, smoothing); }
    if (innerCore.current) innerCore.current.scale.setScalar(.52 + Math.sin(time * 1.45) * .025 + pulse * .08 + (signal.score === undefined ? 0 : signal.score * .035));

    const ringSpeed = processing ? 1.65 : 1;
    if (ringA.current) { ringA.current.rotation.x = THREE.MathUtils.lerp(ringA.current.rotation.x, config.ringTilt[0] + Math.sin(time * .18) * .12, smoothing); ringA.current.rotation.z += delta * .12 * ringSpeed; }
    if (ringB.current) { ringB.current.rotation.y = THREE.MathUtils.lerp(ringB.current.rotation.y, config.ringTilt[1], smoothing); ringB.current.rotation.x += delta * .085 * ringSpeed; }
    if (ringC.current) { ringC.current.rotation.z = THREE.MathUtils.lerp(ringC.current.rotation.z, config.ringTilt[2], smoothing); ringC.current.rotation.y -= delta * .065 * ringSpeed; }

    const realNodes = signal.nodeCount === undefined ? 0 : signal.nodeCount;
    const selectedConceptualNodes = scene === 'regulation-compare' ? signal.jurisdictions.length : 0;
    const nodeCount = compact ? Math.min(8, Math.max(config.conceptualNodes, realNodes)) : Math.min(MAX_NODES, Math.max(config.conceptualNodes, realNodes));
    if (nodes.current) {
      nodes.current.count = nodeCount;
      for (let index = 0; index < nodeCount; index += 1) {
        const source = ((index * 7 + 3) % config.count) * 3; dummy.position.set(displayPoints[source], displayPoints[source + 1], displayPoints[source + 2]);
        const activeNode = index < realNodes || index < selectedConceptualNodes;
        const size = (activeNode ? .068 : .045) * (1 + Math.sin(time * 1.2 + index) * .1 + pulse * .25 + (signal.score === undefined ? 0 : signal.score * .08));
        dummy.scale.setScalar(size); dummy.rotation.set(0, 0, 0); dummy.updateMatrix(); nodes.current.setMatrixAt(index, dummy.matrix);
        nodes.current.setColorAt(index, activeNode ? liveAccent : neutralColor);
      }
      nodes.current.instanceMatrix.needsUpdate = true;
      if (nodes.current.instanceColor) nodes.current.instanceColor.needsUpdate = true;
    }

    const planeCount = compact ? Math.min(config.planes, 5) : config.planes;
    if (planes.current) {
      planes.current.count = planeCount;
      for (let index = 0; index < planeCount; index += 1) {
        const botanical = scene === 'tk-risk'; const scan = (scene === 'document-checker' || scene === 'patentability') && processing ? (time * .32 + index * .12) % 1 : 0;
        dummy.position.set(1.05 + (index % 3) * .34, -1.25 + Math.floor(index / 3) * .32 + scan * .35, -.68 - index * .04);
        dummy.rotation.set(botanical ? .18 : -.15, botanical ? .3 : -.42, botanical ? -.55 + index * .36 : -.08 + index * .025);
        dummy.scale.set(botanical ? .34 : .56, botanical ? .12 : .34, 1); dummy.updateMatrix(); planes.current.setMatrixAt(index, dummy.matrix);
      }
      planes.current.instanceMatrix.needsUpdate = true;
    }
    if (planeMaterial.current) planeMaterial.current.opacity = THREE.MathUtils.lerp(planeMaterial.current.opacity, signal.documentSelected ? .18 : .08, smoothing);

    const travel = (time * (processing ? .42 : .22)) % 1;
    if (activityA.current && lineCount) { activityA.current.visible = processing || pulse > 0; activityA.current.position.set(THREE.MathUtils.lerp(linePositions[0], linePositions[3], travel), THREE.MathUtils.lerp(linePositions[1], linePositions[4], travel), THREE.MathUtils.lerp(linePositions[2], linePositions[5], travel)); }
    if (activityB.current && lineCount > 5) { const base = 30; const back = 1 - travel; activityB.current.visible = processing || pulse > 0; activityB.current.position.set(THREE.MathUtils.lerp(linePositions[base], linePositions[base + 3], back), THREE.MathUtils.lerp(linePositions[base + 1], linePositions[base + 4], back), THREE.MathUtils.lerp(linePositions[base + 2], linePositions[base + 5], back)); }

    group.current.rotation.y += delta * config.rhythm * (processing ? 1.55 : 1);
    group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, pointer.current.y * .11, smoothing * .42); group.current.rotation.z = THREE.MathUtils.lerp(group.current.rotation.z, pointer.current.x * -.075, smoothing * .42);
    group.current.position.x = THREE.MathUtils.lerp(group.current.position.x, config.position[0] + pointer.current.x * .18, smoothing * .46); group.current.position.y = THREE.MathUtils.lerp(group.current.position.y, config.position[1] + pointer.current.y * -.14, smoothing * .46); group.current.position.z = THREE.MathUtils.lerp(group.current.position.z, config.position[2] + pulse * .12, smoothing);
    camera.position.x = THREE.MathUtils.lerp(camera.position.x, config.camera[0] + pointer.current.x * .12, smoothing * .24); camera.position.y = THREE.MathUtils.lerp(camera.position.y, config.camera[1] - pointer.current.y * .08, smoothing * .24); camera.position.z = THREE.MathUtils.lerp(camera.position.z, config.camera[2], smoothing * .3);
    lookTarget.set(config.position[0] * .16, config.position[1] * .1, 0); camera.lookAt(lookTarget);
    if (keyLight.current) { keyLight.current.position.x = 3 + pointer.current.x * 1.8; keyLight.current.position.y = 3.5 - pointer.current.y * 1.5; keyLight.current.intensity = .65 + phaseEnergy * .2 + hoverEnergy + pulse * .35; keyLight.current.color.lerp(targetPrimary, smoothing); }
  });

  return <><ambientLight intensity={.42} /><directionalLight ref={keyLight} position={[3, 3.5, 5]} intensity={.7} color={config.primary} /><group ref={group} position={config.position}>
    <mesh ref={core}><icosahedronGeometry args={[.9, 3]} /><meshBasicMaterial ref={coreMaterial} color={config.primary} transparent opacity={.14} depthWrite={false} /></mesh>
    <mesh ref={innerCore} scale={.52}><icosahedronGeometry args={[1, 2]} /><meshStandardMaterial ref={innerMaterial} color={config.primary} emissive={config.secondary} emissiveIntensity={.45} roughness={.38} metalness={.08} transparent opacity={.72} depthWrite={false} /></mesh>
    <mesh scale={1.04} rotation={[.25, .1, 0]}><icosahedronGeometry args={[.9, 1]} /><meshBasicMaterial ref={wireMaterial} color={config.secondary} transparent opacity={.4} wireframe depthWrite={false} /></mesh>
    <mesh ref={ringA} rotation={[config.ringTilt[0], 0, 0]}><torusGeometry args={[1.36, .009, 3, 80]} /><meshBasicMaterial ref={ringMaterialA} color={config.primary} transparent opacity={.36} depthWrite={false} /></mesh>
    <mesh ref={ringB} rotation={[0, config.ringTilt[1], .35]}><torusGeometry args={[1.72, .007, 3, 80]} /><meshBasicMaterial ref={ringMaterialB} color={config.secondary} transparent opacity={.28} depthWrite={false} /></mesh>
    <mesh ref={ringC} rotation={[.55, 0, config.ringTilt[2]]}><torusGeometry args={[2.05, .005, 3, 80]} /><meshBasicMaterial ref={ringMaterialC} color={config.accent} transparent opacity={.18} depthWrite={false} /></mesh>
    <lineSegments><bufferGeometry ref={linesGeometry}><bufferAttribute attach="attributes-position" args={[linePositions, 3]} /></bufferGeometry><lineBasicMaterial ref={lineMaterial} color={config.secondary} transparent opacity={.14} depthWrite={false} /></lineSegments>
    <points><bufferGeometry ref={pointsGeometry}><bufferAttribute attach="attributes-position" args={[displayPoints, 3]} /></bufferGeometry><pointsMaterial ref={pointMaterial} color={config.primary} size={compact ? .026 : .034} transparent opacity={.78} sizeAttenuation depthWrite={false} /></points>
    <instancedMesh ref={nodes} args={[undefined, undefined, MAX_NODES]}><sphereGeometry args={[1, 8, 8]} /><meshBasicMaterial color={config.accent} transparent opacity={.86} depthWrite={false} /></instancedMesh>
    <instancedMesh ref={planes} args={[undefined, undefined, MAX_PLANES]}><planeGeometry args={[1, 1]} /><meshBasicMaterial ref={planeMaterial} color={config.accent} transparent opacity={.08} wireframe depthWrite={false} /></instancedMesh>
    <mesh ref={activityA}><sphereGeometry args={[.045, 8, 8]} /><meshBasicMaterial color={config.primary} transparent opacity={.9} depthWrite={false} /></mesh><mesh ref={activityB}><sphereGeometry args={[.035, 8, 8]} /><meshBasicMaterial color={config.accent} transparent opacity={.82} depthWrite={false} /></mesh>
  </group></>;
}

export default function PersistentWorkspaceScene({ scene, compact }: { scene: WorkspaceSceneKey; compact: boolean }) {
  const [visible, setVisible] = useState(true);
  useEffect(() => { const update = () => setVisible(document.visibilityState === 'visible'); update(); document.addEventListener('visibilitychange', update); return () => document.removeEventListener('visibilitychange', update); }, []);
  return <Canvas dpr={compact ? [0.8, 1.05] : [1, 1.3]} camera={{ position: [0, 0, 5.4], fov: 46 }} frameloop={visible ? 'always' : 'demand'} gl={{ alpha: true, antialias: !compact, powerPreference: 'low-power' }}><EvidenceField scene={scene} active={visible} compact={compact} /></Canvas>;
}
