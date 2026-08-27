"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { CheckCircle2, ShieldCheck, ArrowRight } from "lucide-react";

export function Pipeline3DPreview() {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [webglSupported, setWebglSupported] = useState<boolean>(true);
  const [activeStage, setActiveStage] = useState<number>(0);

  const stages = [
    { label: "01. DETECT", desc: "CWE Alert Ingest" },
    { label: "02. PATCH", desc: "AST Tree-sitter Synthesis" },
    { label: "03. VERIFY", desc: "gVisor 0-Egress Sandbox" },
    { label: "04. WRITE", desc: "Ed25519 Signed PR" },
  ];

  useEffect(() => {
    try {
      if (
        typeof window === "undefined" ||
        !("WebGLRenderingContext" in window) ||
        process.env.NODE_ENV === "test"
      ) {
        setWebglSupported(false);
        return;
      }
      const testCanvas = document.createElement("canvas");
      const gl =
        testCanvas.getContext("webgl") ||
        testCanvas.getContext("experimental-webgl");
      if (!gl) {
        setWebglSupported(false);
        return;
      }
    } catch {
      setWebglSupported(false);
      return;
    }

    if (!containerRef.current || !canvasRef.current) return;

    const container = containerRef.current;
    const canvas = canvasRef.current;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      35,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    camera.position.set(0, 1.2, 5.2);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x34d399, 1.2);
    dirLight.position.set(2, 4, 3);
    scene.add(dirLight);

    const group = new THREE.Group();
    scene.add(group);

    // 4 Horizontal Gate Waypoints (X: -2.1, -0.7, 0.7, 2.1)
    const xPositions = [-2.1, -0.7, 0.7, 2.1];
    const gateMeshes: THREE.Mesh[] = [];

    // Connecting Rail Line
    const railPoints = [
      new THREE.Vector3(-2.4, 0, 0),
      new THREE.Vector3(2.4, 0, 0),
    ];
    const railGeo = new THREE.BufferGeometry().setFromPoints(railPoints);
    const railMat = new THREE.LineBasicMaterial({
      color: 0x272730,
      transparent: true,
      opacity: 0.8,
    });
    group.add(new THREE.Line(railGeo, railMat));

    xPositions.forEach((x, idx) => {
      const ringGeo = new THREE.RingGeometry(0.3, 0.36, 24);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x272730,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.8,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.position.set(x, 0, 0);
      ringMesh.rotation.y = Math.PI * 0.2;
      group.add(ringMesh);
      gateMeshes.push(ringMesh);
    });

    // Animated Transit Capsule
    const capsuleGeo = new THREE.OctahedronGeometry(0.16, 0);
    const capsuleMat = new THREE.MeshStandardMaterial({
      color: 0x34d399,
      emissive: 0x064e3b,
      emissiveIntensity: 0.5,
    });
    const capsuleMesh = new THREE.Mesh(capsuleGeo, capsuleMat);
    group.add(capsuleMesh);

    // Parallax
    let mouseX = 0;
    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 0.4;
    };
    container.addEventListener("mousemove", handleMouseMove);

    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    const observer = new ResizeObserver(handleResize);
    observer.observe(container);

    let frameId: number;
    let t = 0;

    const animate = () => {
      frameId = requestAnimationFrame(animate);

      // Smooth camera tilt
      group.rotation.y += (mouseX - group.rotation.y) * 0.05;

      // Capsule linear loop across X
      t += 0.005;
      if (t > 1.0) t = 0;

      const currentX = -2.4 + t * 4.8;
      capsuleMesh.position.set(currentX, Math.sin(t * Math.PI * 4) * 0.08, 0);
      capsuleMesh.rotation.x += 0.02;
      capsuleMesh.rotation.y += 0.03;

      // Identify active gate
      const activeIdx = xPositions.findIndex(
        (x) => Math.abs(currentX - x) < 0.45
      );
      if (activeIdx !== -1) {
        setActiveStage(activeIdx);
      }

      // Highlight passed gates
      gateMeshes.forEach((mesh, idx) => {
        const isPassed = currentX >= xPositions[idx] - 0.1;
        (mesh.material as THREE.MeshBasicMaterial).color.setHex(
          isPassed ? 0x34d399 : 0x272730
        );
      });

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(frameId);
      observer.disconnect();
      container.removeEventListener("mousemove", handleMouseMove);
      renderer.dispose();
      railGeo.dispose();
      capsuleGeo.dispose();
      capsuleMat.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full rounded-md border border-border-subtle bg-zinc-950/80 shadow-xl overflow-hidden font-mono text-xs select-none min-h-[220px] flex flex-col justify-between"
      aria-label="3D Execution Stages Visualizer"
    >
      {webglSupported ? (
        <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-zinc-500 text-xs">
          Stage Pipeline: DETECT → PATCH → VERIFY → WRITE
        </div>
      )}

      {/* Top Strip */}
      <div className="relative z-10 p-3 bg-zinc-950/60 backdrop-blur-sm border-b border-border-subtle flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-subtle" />
          <span className="text-[11px] font-semibold text-zinc-200 uppercase tracking-wider">
            3D Pipeline Transit
          </span>
        </div>
        <span className="text-[10px] text-emerald-400 font-mono">
          STAGE 0{activeStage + 1} ACTIVE
        </span>
      </div>

      {/* Bottom Stage Callouts */}
      <div className="relative z-10 p-3 bg-zinc-950/80 backdrop-blur-sm border-t border-border-subtle grid grid-cols-2 sm:grid-cols-4 gap-2">
        {stages.map((stg, idx) => {
          const isActive = activeStage === idx;
          return (
            <div
              key={stg.label}
              className={`p-1.5 rounded border transition-all duration-150 ${
                isActive
                  ? "bg-zinc-900 border-zinc-700 text-zinc-100 shadow-sm ring-1 ring-emerald-500/20"
                  : "bg-zinc-950/40 border-transparent text-zinc-500"
              }`}
            >
              <div
                className={`text-[10px] font-bold ${
                  isActive ? "text-emerald-300" : "text-zinc-400"
                }`}
              >
                {stg.label}
              </div>
              <div className="text-[9px] text-zinc-500 truncate">{stg.desc}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
