import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Environment } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import * as THREE from 'three';

function DNAHelix() {
    const group = useRef<THREE.Group>(null);

    // Smooth, continuous rotation
    useFrame((state, delta) => {
        if (group.current) {
            group.current.rotation.y += delta * 0.15;
        }
    });

    const { points, connectionDots } = useMemo(() => {
        const count = 40; // Number of base pairs
        const radius = 3; // Constant radius (Cylindrical)
        const height = 14;
        const turns = 3;

        const pts = [];
        const connDots = [];

        for (let i = 0; i < count; i++) {
            const t = i / (count - 1);
            const angle = t * Math.PI * 2 * turns;
            const y = (t - 0.5) * height;

            // Strand 1 position
            const x1 = Math.cos(angle) * radius;
            const z1 = Math.sin(angle) * radius;
            const start = new THREE.Vector3(x1, y, z1);

            // Strand 2 position (offset by PI)
            const x2 = Math.cos(angle + Math.PI) * radius;
            const z2 = Math.sin(angle + Math.PI) * radius;
            const end = new THREE.Vector3(x2, y, z2);

            const color1 = i % 2 === 0 ? '#3b82f6' : '#06b6d4'; // Alternating Blue/Cyan
            const color2 = i % 2 === 0 ? '#06b6d4' : '#3b82f6';

            pts.push({ pos: [x1, y, z1], color: color1 });
            pts.push({ pos: [x2, y, z2], color: color2 });

            // Dotted Connections
            // Create dots between the two strands (increased density)
            const dotsPerConnection = 11;
            for (let j = 1; j < dotsPerConnection; j++) {
                const alpha = j / dotsPerConnection;
                const dotPos = new THREE.Vector3().lerpVectors(start, end, alpha);

                connDots.push({
                    pos: [dotPos.x, dotPos.y, dotPos.z],
                    color: '#475569' // Slate-600 for connection dots
                });
            }
        }
        return { points: pts, connectionDots: connDots };
    }, []);

    return (
        <group ref={group} rotation={[0, 0, Math.PI / 6]}>
            {/* Main Strand Particles (Nucleotides) */}
            {points.map((pt, i) => (
                <mesh key={`pt-${i}`} position={pt.pos as [number, number, number]}>
                    <sphereGeometry args={[0.15, 16, 16]} />
                    <meshStandardMaterial
                        color={pt.color}
                        emissive={pt.color}
                        emissiveIntensity={0.8}
                        transparent
                        opacity={0.9}
                        roughness={0.2}
                    />
                </mesh>
            ))}

            {/* Connection Dots (The "Rungs") */}
            {connectionDots.map((dot, i) => (
                <mesh key={`conn-dot-${i}`} position={dot.pos as [number, number, number]}>
                    <sphereGeometry args={[0.05, 8, 8]} />
                    <meshStandardMaterial
                        color={dot.color}
                        transparent
                        opacity={0.5}
                        emissive={dot.color}
                        emissiveIntensity={0.3}
                    />
                </mesh>
            ))}
        </group>
    );
}

export default function Background3D() {
    return (
        <div className="fixed inset-0 z-0 pointer-events-none opacity-40">
            <Canvas gl={{ antialias: true, alpha: true }} camera={{ position: [0, 0, 12], fov: 45 }}>
                <ambientLight intensity={0.1} />
                <pointLight position={[10, 10, 10]} intensity={0.5} />
                <pointLight position={[-10, -5, -5]} intensity={0.5} color="#3b82f6" />

                <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
                    <DNAHelix />
                </Float>

                <Environment preset="city" />

                <EffectComposer>
                    <Bloom
                        luminanceThreshold={0.4}
                        mipmapBlur
                        intensity={1.0}
                        radius={0.5}
                    />
                </EffectComposer>
            </Canvas>
        </div>
    );
}
