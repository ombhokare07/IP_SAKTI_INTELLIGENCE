'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Line } from '@react-three/drei';
import * as THREE from 'three';

const nodePositions: [number, number, number][] = [
  [-1.65, .85, .1], [1.75, .65, -.2], [-1.35, -1.05, .2], [1.4, -1.1, .35], [0, 1.75, -.2], [0, -1.75, -.15],
];

function Network({ active }: { active: boolean }) {
  const group = useRef<THREE.Group>(null);
  const particles = useMemo(() => {
    const values = new Float32Array(66 * 3);
    for (let index = 0; index < 66; index += 1) {
      const radius = 2.15 + ((index * 13) % 19) / 26;
      const angle = index * 2.399;
      values[index * 3] = Math.cos(angle) * radius;
      values[index * 3 + 1] = Math.sin(angle * .71) * 1.8;
      values[index * 3 + 2] = Math.sin(angle) * radius * .36;
    }
    return values;
  }, []);

  useFrame((state, delta) => {
    if (!active || !group.current) return;
    group.current.rotation.y += delta * .055;
    group.current.rotation.x = Math.sin(state.clock.elapsedTime * .18) * .045;
  });

  return <group ref={group}>
    <Float speed={.55} rotationIntensity={.12} floatIntensity={.18}>
      <mesh>
        <icosahedronGeometry args={[1.14, 3]} />
        <meshPhysicalMaterial color="#17345b" emissive="#172c67" emissiveIntensity={.42} transparent opacity={.72} roughness={.18} metalness={.2} transmission={.16} thickness={.7} />
      </mesh>
      <mesh scale={1.03}>
        <icosahedronGeometry args={[1.14, 2]} />
        <meshBasicMaterial color="#5fe8ff" transparent opacity={.22} wireframe />
      </mesh>
      <mesh scale={.62}>
        <icosahedronGeometry args={[1, 1]} />
        <meshBasicMaterial color="#866cff" transparent opacity={.26} />
      </mesh>
    </Float>

    <mesh rotation={[Math.PI / 2.2, 0, .2]}>
      <torusGeometry args={[1.72, .012, 5, 96]} />
      <meshBasicMaterial color="#22d3ee" transparent opacity={.42} />
    </mesh>
    <mesh rotation={[Math.PI / 1.8, .5, 1]}>
      <torusGeometry args={[2.05, .009, 5, 96]} />
      <meshBasicMaterial color="#7c5cff" transparent opacity={.3} />
    </mesh>

    {nodePositions.map((position, index) => <group key={position.join(':')} position={position}>
      <mesh>
        <sphereGeometry args={[index % 2 ? .08 : .105, 12, 12]} />
        <meshBasicMaterial color={index % 3 === 0 ? '#34d399' : index % 3 === 1 ? '#22d3ee' : '#a78bfa'} />
      </mesh>
      <pointLight color={index % 2 ? '#22d3ee' : '#7c5cff'} intensity={1.2} distance={1.1} />
      <Line points={[[0, 0, 0], [-position[0], -position[1], -position[2]]]} color={index % 2 ? '#38bdf8' : '#8b5cf6'} transparent opacity={.18} lineWidth={.6} />
    </group>)}

    <group position={[1.55, -1.25, -.05]} rotation={[0, 0, -.45]}>
      {[0, 1, 2].map((index) => <mesh key={index} position={[index * .22, index * .2, 0]} rotation={[0, 0, index % 2 ? .7 : -.4]} scale={[.3, .11, .045]}>
        <sphereGeometry args={[1, 12, 8]} />
        <meshBasicMaterial color="#34d399" transparent opacity={.38 - index * .05} />
      </mesh>)}
    </group>

    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[particles, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#93c5fd" size={.022} transparent opacity={.46} sizeAttenuation />
    </points>
  </group>;
}

export default function IntelligenceScene({ className = '' }: { className?: string }) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const update = () => setVisible(document.visibilityState === 'visible');
    update();
    document.addEventListener('visibilitychange', update);
    return () => document.removeEventListener('visibilitychange', update);
  }, []);

  return <div className={`intelligence-canvas ${className}`} aria-hidden="true">
    <Canvas
      dpr={[1, 1.4]}
      camera={{ position: [0, 0, 5.1], fov: 42 }}
      frameloop={visible ? 'always' : 'demand'}
      gl={{ alpha: true, antialias: true, powerPreference: 'low-power' }}
    >
      <ambientLight intensity={.5} />
      <pointLight position={[3, 4, 5]} intensity={4} color="#67e8f9" />
      <pointLight position={[-4, -2, 3]} intensity={3.5} color="#7c5cff" />
      <Network active={visible} />
    </Canvas>
  </div>;
}

