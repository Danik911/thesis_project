'use client';

import { useRef, useMemo, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Cylinder, Float, MeshTransmissionMaterial } from '@react-three/drei';
import * as THREE from 'three';

interface MoleculeProps {
    scale?: number;
    color?: string;
    position?: [number, number, number];
}

// CPK-inspired color scheme for abstract chemical elements
const ELEMENT_COLORS: Record<string, string> = {
    'C': '#909090',  // Carbon - Gray
    'N': '#3050F8',  // Nitrogen - Blue
    'O': '#FF0D0D',  // Oxygen - Red
    'H': '#FFFFFF',  // Hydrogen - White
};

// Define stable, deterministic 3D molecular structure
const MOLECULAR_STRUCTURE = [
    // Two core atoms (representing Carbon centers)
    {
        position: [-0.8, 0, 0] as [number, number, number],
        size: 0.6,
        element: 'C',
        type: 'core'
    },
    {
        position: [0.8, 0, 0] as [number, number, number],
        size: 0.6,
        element: 'C',
        type: 'core',
        parent: [-0.8, 0, 0] as [number, number, number]
    },

    // Peripheral atoms in a stable 3D ring (representing Nitrogen/Oxygen)
    // Positioned at regular intervals with tetrahedral-inspired angles
    {
        position: [-1.8, 1.2, 0.6] as [number, number, number],
        size: 0.35,
        element: 'N',
        type: 'peripheral',
        parent: [-0.8, 0, 0] as [number, number, number]
    },
    {
        position: [0.2, 1.8, -0.4] as [number, number, number],
        size: 0.35,
        element: 'O',
        type: 'peripheral',
        parent: [-0.8, 0, 0] as [number, number, number]
    },
    {
        position: [1.8, 1.2, 0.6] as [number, number, number],
        size: 0.35,
        element: 'N',
        type: 'peripheral',
        parent: [0.8, 0, 0] as [number, number, number]
    },
    {
        position: [-0.2, -1.8, 0.5] as [number, number, number],
        size: 0.35,
        element: 'O',
        type: 'peripheral',
        parent: [-0.8, 0, 0] as [number, number, number]
    },
    {
        position: [1.6, -1.4, -0.3] as [number, number, number],
        size: 0.35,
        element: 'N',
        type: 'peripheral',
        parent: [0.8, 0, 0] as [number, number, number]
    },

    // Additional hydrogen-like atoms for complexity
    {
        position: [-2.2, -0.8, -0.7] as [number, number, number],
        size: 0.25,
        element: 'H',
        type: 'peripheral',
        parent: [-0.8, 0, 0] as [number, number, number]
    },
    {
        position: [2.2, -0.6, 0.8] as [number, number, number],
        size: 0.25,
        element: 'H',
        type: 'peripheral',
        parent: [0.8, 0, 0] as [number, number, number]
    },
];

export default function Molecule({ scale = 1, color = "#60A5FA", position = [0, 0, 0] }: MoleculeProps) {
    const groupRef = useRef<THREE.Group>(null);
    const [hovered, setHover] = useState(false);
    const rotationSpeed = useRef(1);
    const currentScale = useRef(scale);

    useFrame((state, delta) => {
        if (groupRef.current) {
            // Smoothly interpolate rotation speed
            const targetSpeed = hovered ? 3 : 1;
            rotationSpeed.current = THREE.MathUtils.lerp(rotationSpeed.current, targetSpeed, 0.05);

            groupRef.current.rotation.y += delta * 0.2 * rotationSpeed.current;
            groupRef.current.rotation.x += delta * 0.1 * rotationSpeed.current;
            groupRef.current.rotation.z += delta * 0.05 * rotationSpeed.current;

            // Smoothly interpolate scale
            const targetScale = hovered ? scale * 1.2 : scale;
            currentScale.current = THREE.MathUtils.lerp(currentScale.current, targetScale, 0.1);
            groupRef.current.scale.setScalar(currentScale.current);
        }
    });

    // Use deterministic structure
    const atoms = useMemo(() => MOLECULAR_STRUCTURE, []);

    return (
        <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5} position={position}>
            <group
                ref={groupRef}
                scale={scale}
                onPointerOver={() => setHover(true)}
                onPointerOut={() => setHover(false)}
            >
                {atoms.map((atom, i) => (
                    <group key={i}>
                        <Sphere args={[atom.size, 32, 32]} position={atom.position}>
                            <MeshTransmissionMaterial
                                // Glass effect properties
                                transmission={1}              // Full transparency
                                thickness={0.3}               // Subtle refraction depth
                                roughness={0}                 // Polished glass surface
                                ior={1.3}                     // Index of refraction (glass ~1.5)
                                chromaticAberration={0.02}    // Rainbow edge effect

                                // Color based on element type or prop color for cores
                                color={atom.type === 'core' ? color : ELEMENT_COLORS[atom.element]}

                                // Emissive glow for bloom effect
                                emissive={atom.type === 'core' ? color : ELEMENT_COLORS[atom.element]}
                                emissiveIntensity={0.15}

                                // Additional glass properties
                                backside={true}
                                attenuationDistance={0.5}
                                attenuationColor="#ffffff"
                            />
                        </Sphere>
                        {atom.parent && (
                            <Bond
                                start={atom.parent}
                                end={atom.position}
                                color={atom.type === 'core' ? color : ELEMENT_COLORS[atom.element]}
                            />
                        )}
                    </group>
                ))}
            </group>
        </Float>
    );
}

function Bond({ start, end, color }: { start: [number, number, number]; end: [number, number, number]; color: string }) {
    const startVec = new THREE.Vector3(...start);
    const endVec = new THREE.Vector3(...end);
    const direction = new THREE.Vector3().subVectors(endVec, startVec);
    const length = direction.length();
    const position = new THREE.Vector3().addVectors(startVec, endVec).multiplyScalar(0.5);

    // Calculate rotation to align cylinder with direction
    const quaternion = new THREE.Quaternion();
    quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
    const rotation = new THREE.Euler().setFromQuaternion(quaternion);

    return (
        <Cylinder args={[0.12, 0.12, length, 16]} position={[position.x, position.y, position.z]} rotation={[rotation.x, rotation.y, rotation.z]}>
            <MeshTransmissionMaterial
                transmission={0.9}
                thickness={0.2}
                roughness={0.1}
                ior={1.3}
                color={color}
                emissive={color}
                emissiveIntensity={0.1}
                opacity={0.85}
                transparent={true}
                backside={true}
            />
        </Cylinder>
    );
}
