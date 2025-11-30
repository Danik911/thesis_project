import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Environment, PerspectiveCamera } from '@react-three/drei';
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

    const { points, connections } = useMemo(() => {
        const count = 30; // Number of base pairs
        const radius = 2.5;
        const height = 12;
        const turns = 2.5;

        const pts = [];
        const conns = [];

        for (let i = 0; i < count; i++) {
            const t = i / (count - 1);
            const angle = t * Math.PI * 2 * turns;
            const y = (t - 0.5) * height;

            // Strand 1 position
            const x1 = Math.cos(angle) * radius;
            const z1 = Math.sin(angle) * radius;

            // Strand 2 position (offset by PI)
            const x2 = Math.cos(angle + Math.PI) * radius;
            const z2 = Math.sin(angle + Math.PI) * radius;

            const color1 = i % 2 === 0 ? '#3b82f6' : '#06b6d4'; // Alternating Blue/Cyan
            const color2 = i % 2 === 0 ? '#06b6d4' : '#3b82f6';

            pts.push({ pos: [x1, y, z1], color: color1 });
            pts.push({ pos: [x2, y, z2], color: color2 });

            // Connection between strands
            conns.push({
                start: [x1, y, z1],
                end: [x2, y, z2],
                color: '#475569' // Slate-600 for subtle connections
            });
        }
        return { points: pts, connections: conns };
    }, []);

    return (
        <group ref={group} rotation={[0, 0, Math.PI / 6]}>
            {/* Particles (Nucleotides) */}
            {points.map((pt, i) => (
                <mesh key={`pt-${i}`} position={pt.pos as [number, number, number]}>
                    <sphereGeometry args={[0.12, 16, 16]} />
                    <meshStandardMaterial
                        color={pt.color}
                        emissive={pt.color}
                        emissiveIntensity={0.8}
                        transparent
                        opacity={0.8}
                        roughness={0.2}
                    />
                </mesh>
            ))}

            {/* Connections (Base Pairs) - using thin cylinders */}
            {connections.map((conn, i) => {
                const start = new THREE.Vector3(...(conn.start as [number, number, number]));
                const end = new THREE.Vector3(...(conn.end as [number, number, number]));
                const length = start.distanceTo(end);
                const position = start.clone().add(end).multiplyScalar(0.5);
                const orientation = new THREE.Matrix4();
                orientation.lookAt(start, end, new THREE.Vector3(0, 1, 0));
                const rotation = new THREE.Euler();
                rotation.setFromRotationMatrix(orientation);

                return (
                    <mesh
                        key={`conn-${i}`}
                        position={position}
                        rotation={[rotation.x + Math.PI / 2, rotation.y, rotation.z]} // Adjust cylinder rotation
                    >
                        <cylinderGeometry args={[0.02, 0.02, length, 8]} />
                        <meshStandardMaterial
                            color={conn.color}
                            transparent
                            opacity={0.3}
                            emissive={conn.color}
                            emissiveIntensity={0.2}
                        />
                    </mesh>
                );
            })}
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
