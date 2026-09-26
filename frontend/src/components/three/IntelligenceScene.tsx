'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';

const nodePositions: [number, number, number][] = [
  [-1.65, .85, .1], [1.75, .65, -.2], [-1.35, -1.05, .2], [1.4, -1.1, .35], [0, 1.75, -.2], [0, -1.75, -.15],
];

type LoginScenePhase = 'idle' | 'signing-in' | 'success';

function Network({ active, phase, hover }: { active: boolean; phase: LoginScenePhase; hover: string }) {
  const group = useRef<THREE.Group>(null); const core = useRef<THREE.Mesh>(null);
  const ringA = useRef<THREE.Mesh>(null); const ringB = useRef<THREE.Mesh>(null); const ringC = useRef<THREE.Mesh>(null);
  const material = useRef<THREE.MeshStandardMaterial>(null); const pointsGeometry = useRef<THREE.BufferGeometry>(null);
  const pointer = useRef({ x: 0, y: 0 }); const phaseChangedAt = useRef(0); const previousPhase = useRef(phase);
  const baseParticles = useMemo(() => {
    const values = new Float32Array(66 * 3);
    for (let index = 0; index < 66; index += 1) { const radius = 2.15 + ((index * 13) % 19) / 26; const angle = index * 2.399; values[index * 3] = Math.cos(angle) * radius; values[index * 3 + 1] = Math.sin(angle * .71) * 1.8; values[index * 3 + 2] = Math.sin(angle) * radius * .36; }
    return values;
  }, []);
  const particles = useMemo(() => new Float32Array(baseParticles), [baseParticles]);

  useEffect(() => {
    const move = (event: PointerEvent) => { pointer.current.x = event.clientX / window.innerWidth - .5; pointer.current.y = event.clientY / window.innerHeight - .5; };
    window.addEventListener('pointermove', move, { passive: true }); return () => window.removeEventListener('pointermove', move);
  }, []);

  useFrame((state, delta) => {
    if (!active || !group.current) return;
    if (previousPhase.current !== phase) { previousPhase.current = phase; phaseChangedAt.current = state.clock.elapsedTime; }
    const time = state.clock.elapsedTime; const busy = phase === 'signing-in'; const successAge = phase === 'success' ? time - phaseChangedAt.current : 99;
    const successPulse = successAge < .55 ? Math.sin(Math.min(1, successAge / .55) * Math.PI) : 0; const energy = busy ? 1.65 : 1;
    group.current.rotation.y += delta * .075 * energy; group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, pointer.current.y * .12 + Math.sin(time * .18) * .04, delta * 2.4); group.current.rotation.z = THREE.MathUtils.lerp(group.current.rotation.z, pointer.current.x * -.09, delta * 2.4);
    group.current.position.x = THREE.MathUtils.lerp(group.current.position.x, pointer.current.x * .16, delta * 2.2); group.current.position.y = THREE.MathUtils.lerp(group.current.position.y, pointer.current.y * -.12, delta * 2.2);
    if (core.current) core.current.scale.setScalar(1 + Math.sin(time * 1.5) * .035 + successPulse * .16 + (hover ? .035 : 0));
    if (material.current) material.current.emissiveIntensity = .48 + (busy ? .28 : 0) + successPulse * .8 + (hover ? .12 : 0);
    if (ringA.current) { ringA.current.rotation.z += delta * .14 * energy; ringA.current.rotation.x = .68 + Math.sin(time * .2) * .12; }
    if (ringB.current) { ringB.current.rotation.x -= delta * .1 * energy; ringB.current.rotation.y = .52 + Math.cos(time * .17) * .1; }
    if (ringC.current) { ringC.current.rotation.y += delta * .075 * energy; ringC.current.rotation.z = 1.05 + Math.sin(time * .14) * .09; }
    for (let index = 0; index < 66; index += 1) { const offset = index * 3; const drift = Math.sin(time * (.32 + index % 7 * .025) + index * 1.37) * .018; const convergence = busy ? .93 : 1; particles[offset] = baseParticles[offset] * convergence + drift; particles[offset + 1] = baseParticles[offset + 1] * convergence + Math.cos(time * .28 + index) * .014; particles[offset + 2] = baseParticles[offset + 2] + drift * 1.6; }
    const attribute = pointsGeometry.current?.attributes.position as THREE.BufferAttribute | undefined; if (attribute) attribute.needsUpdate = true;
  });

  return <group ref={group}>
    <mesh ref={core}><icosahedronGeometry args={[1.14, 3]} /><meshStandardMaterial ref={material} color="#17345b" emissive="#2756aa" emissiveIntensity={.5} transparent opacity={.76} roughness={.3} metalness={.12} depthWrite={false} /></mesh>
    <mesh scale={1.03}><icosahedronGeometry args={[1.14, 2]} /><meshBasicMaterial color="#5fe8ff" transparent opacity={.25} wireframe depthWrite={false} /></mesh>
    <mesh scale={.62}><icosahedronGeometry args={[1, 1]} /><meshBasicMaterial color="#866cff" transparent opacity={.3} depthWrite={false} /></mesh>
    <mesh ref={ringA} rotation={[.68, 0, .2]}><torusGeometry args={[1.72, .012, 5, 96]} /><meshBasicMaterial color="#22d3ee" transparent opacity={.46} depthWrite={false} /></mesh>
    <mesh ref={ringB} rotation={[0, .52, 1]}><torusGeometry args={[2.05, .009, 5, 96]} /><meshBasicMaterial color="#7c5cff" transparent opacity={.34} depthWrite={false} /></mesh>
    <mesh ref={ringC} rotation={[.4, .25, 1.05]}><torusGeometry args={[2.38, .006, 4, 96]} /><meshBasicMaterial color="#34d399" transparent opacity={.2} depthWrite={false} /></mesh>
    {nodePositions.map((position, index) => <group key={position.join(':')} position={position}><mesh><sphereGeometry args={[index % 2 ? .08 : .105, 10, 10]} /><meshBasicMaterial color={index % 3 === 0 ? '#34d399' : index % 3 === 1 ? '#22d3ee' : '#a78bfa'} /></mesh><Line points={[[0, 0, 0], [-position[0], -position[1], -position[2]]]} color={index % 2 ? '#38bdf8' : '#8b5cf6'} transparent opacity={.2} lineWidth={.6} /></group>)}
    <group position={[1.55, -1.25, -.05]} rotation={[0, 0, -.45]}>{[0, 1, 2].map((index) => <mesh key={index} position={[index * .22, index * .2, 0]} rotation={[0, 0, index % 2 ? .7 : -.4]} scale={[.3, .11, .045]}><sphereGeometry args={[1, 12, 8]} /><meshBasicMaterial color="#34d399" transparent opacity={.38 - index * .05} /></mesh>)}</group>
    <points><bufferGeometry ref={pointsGeometry}><bufferAttribute attach="attributes-position" args={[particles, 3]} /></bufferGeometry><pointsMaterial color="#93c5fd" size={.024} transparent opacity={.52} sizeAttenuation depthWrite={false} /></points>
  </group>;
}

export default function IntelligenceScene({ className = '', phase = 'idle', hover = '' }: { className?: string; phase?: LoginScenePhase; hover?: string }) {
  const [visible, setVisible] = useState(true);
  useEffect(() => { const update = () => setVisible(document.visibilityState === 'visible'); update(); document.addEventListener('visibilitychange', update); return () => document.removeEventListener('visibilitychange', update); }, []);
  return <div className={`intelligence-canvas ${className}`} aria-hidden="true"><Canvas dpr={[1, 1.4]} camera={{ position: [0, 0, 5.1], fov: 42 }} frameloop={visible ? 'always' : 'demand'} gl={{ alpha: true, antialias: true, powerPreference: 'low-power' }}><ambientLight intensity={.48} /><directionalLight position={[3, 4, 5]} intensity={1.1} color="#8cefff" /><Network active={visible} phase={phase} hover={hover} /></Canvas></div>;
}
