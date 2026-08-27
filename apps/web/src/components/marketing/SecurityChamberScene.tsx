"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { ShieldCheck, CheckCircle2, XCircle, Check, X } from "lucide-react";

type ChamberMode = "verified" | "blocked";

interface GateDef {
  id: string;
  number: string;
  name: string;
  label: string;
  y: number;
}

const GATES: GateDef[] = [
  { id: "ast",    number: "01", name: "AST SYNTAX",   label: "AST",     y:  2.2 },
  { id: "sandbox",number: "02", name: "SANDBOX",       label: "SANDBOX", y:  0.8 },
  { id: "tests",  number: "03", name: "REGRESSION",    label: "TESTS",   y: -0.6 },
  { id: "policy", number: "04", name: "POLICY GATE",   label: "POLICY",  y: -2.0 },
  { id: "proof",  number: "05", name: "CRYPTO SEAL",   label: "PROOF",   y: -3.2 },
];

export function SecurityChamberScene() {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [mode, setMode] = useState<ChamberMode>("verified");
  const [webglSupported, setWebglSupported] = useState<boolean>(true);
  const [isLoaded, setIsLoaded] = useState<boolean>(false);

  const modeRef = useRef<ChamberMode>(mode);
  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    // Check WebGL support safely
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

    // --- THREE.JS SCENE SETUP ---
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x09090b, 0.045);

    // Cinematic camera — narrower FOV, more depth
    const camera = new THREE.PerspectiveCamera(
      32,
      container.clientWidth / container.clientHeight,
      0.1,
      120
    );
    const initialCamPos = new THREE.Vector3(2.4, 1.6, 10.5);
    camera.position.copy(initialCamPos);
    camera.lookAt(0, -0.5, 0);

    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));

    // --- LIGHTING ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.55);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0x34d399, 2.0);
    keyLight.position.set(5, 10, 7);
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 0.8);
    rimLight.position.set(-6, -4, -5);
    scene.add(rimLight);

    const patchPointLight = new THREE.PointLight(0x34d399, 2.8, 6.0);
    scene.add(patchPointLight);

    // --- 3D VERIFICATION CHAMBER STRUCTURE ---
    const chamberGroup = new THREE.Group();
    scene.add(chamberGroup);

    // Shared materials (reused across geometry instances)
    const pylonMat = new THREE.MeshStandardMaterial({
      color: 0x1a1a22,
      metalness: 0.92,
      roughness: 0.18,
    });
    const pylonEdgeMat = new THREE.LineBasicMaterial({
      color: 0x2e2e3c,
      transparent: true,
      opacity: 0.75,
    });
    const girderMat = new THREE.MeshStandardMaterial({
      color: 0x111118,
      metalness: 0.95,
      roughness: 0.22,
    });
    const girderEdgeMat = new THREE.LineBasicMaterial({ color: 0x48485a });

    // 1. Four Massive Structural Pylons
    const pylonGeo = new THREE.BoxGeometry(0.14, 7.2, 0.14);
    const pylonPositions: [number, number, number][] = [
      [-2.1, -0.5, -1.15],
      [ 2.1, -0.5, -1.15],
      [-2.1, -0.5,  1.15],
      [ 2.1, -0.5,  1.15],
    ];
    const pylonEdgeGeo = new THREE.EdgesGeometry(pylonGeo);
    pylonPositions.forEach(([x, y, z]) => {
      const pylon = new THREE.Mesh(pylonGeo, pylonMat);
      pylon.position.set(x, y, z);
      chamberGroup.add(pylon);
      const pEdges = new THREE.LineSegments(pylonEdgeGeo, pylonEdgeMat);
      pylon.add(pEdges);
    });

    // 2. Heavy Top & Bottom Girders
    const girderGeo = new THREE.BoxGeometry(4.36, 0.14, 2.46);
    const girderEdgeGeo = new THREE.EdgesGeometry(girderGeo);
    [3.1, -4.1].forEach((y) => {
      const girder = new THREE.Mesh(girderGeo, girderMat);
      girder.position.set(0, y, 0);
      chamberGroup.add(girder);
      girder.add(new THREE.LineSegments(girderEdgeGeo, girderEdgeMat));
    });

    // 3. Five 3D Extruded Gate Portals
    interface GateObject {
      id: string;
      group: THREE.Group;
      aperture: THREE.Mesh;
      border: THREE.LineSegments;
      glowLight: THREE.PointLight;
      y: number;
    }

    const gateObjects: GateObject[] = [];

    // Shared gate geometries
    const deckGeo = new THREE.BoxGeometry(3.8, 0.14, 2.1);
    const deckEdgeGeo = new THREE.EdgesGeometry(deckGeo);
    const apertureGeo = new THREE.TorusGeometry(0.78, 0.052, 14, 36);

    GATES.forEach((gate) => {
      const gGroup = new THREE.Group();
      gGroup.position.set(0, gate.y, 0);

      const deckMat = new THREE.MeshBasicMaterial({ color: 0x0e0e14 });
      const deckMesh = new THREE.Mesh(deckGeo, deckMat);
      gGroup.add(deckMesh);

      const borderLine = new THREE.LineSegments(
        deckEdgeGeo,
        new THREE.LineBasicMaterial({
          color: 0x212130,
          transparent: true,
          opacity: 0.8,
        })
      );
      gGroup.add(borderLine);

      // Inner Glowing Aperture Torus
      const apertureMat = new THREE.MeshStandardMaterial({
        color: 0x23232e,
        emissive: 0x09090b,
        emissiveIntensity: 0.15,
        roughness: 0.22,
        metalness: 0.92,
      });
      const apertureMesh = new THREE.Mesh(apertureGeo, apertureMat);
      apertureMesh.rotation.x = Math.PI * 0.5;
      gGroup.add(apertureMesh);

      const gateLight = new THREE.PointLight(0x34d399, 0.0, 3.5);
      gGroup.add(gateLight);

      chamberGroup.add(gGroup);

      gateObjects.push({
        id: gate.id,
        group: gGroup,
        aperture: apertureMesh,
        border: borderLine,
        glowLight: gateLight,
        y: gate.y,
      });
    });

    // Patch travel range — declared here so destMesh can reference endY
    const startY = 3.8;
    const endY = -4.0;
    const failHaltY = GATES[2].y + 0.34;

    // 4. Fail-Closed Barrier Plate (Gate 03)
    const barrierGroup = new THREE.Group();
    barrierGroup.position.set(0, GATES[2].y + 0.08, 0);

    const barrierPlateGeo = new THREE.BoxGeometry(3.6, 0.10, 2.0);
    const barrierPlateMat = new THREE.MeshStandardMaterial({
      color: 0x991b1b,
      emissive: 0xb91c1c,
      emissiveIntensity: 0.85,
      transparent: true,
      opacity: 0.0,
      roughness: 0.18,
      metalness: 0.92,
    });
    const barrierPlate = new THREE.Mesh(barrierPlateGeo, barrierPlateMat);
    barrierGroup.add(barrierPlate);

    const barrierLattice = new THREE.LineSegments(
      new THREE.EdgesGeometry(barrierPlateGeo),
      new THREE.LineBasicMaterial({
        color: 0xf87171,
        transparent: true,
        opacity: 0.0,
      })
    );
    barrierGroup.add(barrierLattice);
    chamberGroup.add(barrierGroup);

    // 5. 3D Animated Patch Node (Crystal Core + Gyroscope Rings)
    // Larger octahedron (0.42 vs 0.34) for clearer visibility
    const patchGroup = new THREE.Group();
    chamberGroup.add(patchGroup);

    const patchCoreGeo = new THREE.OctahedronGeometry(0.42, 0);
    const patchCoreMat = new THREE.MeshStandardMaterial({
      color: 0x34d399,
      emissive: 0x059669,
      emissiveIntensity: 1.3,
      roughness: 0.06,
      metalness: 0.88,
    });
    const patchCore = new THREE.Mesh(patchCoreGeo, patchCoreMat);
    patchGroup.add(patchCore);

    const ringGeo = new THREE.TorusGeometry(0.60, 0.022, 10, 32);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x6ee7b7 });
    const ring1 = new THREE.Mesh(ringGeo, ringMat);
    patchGroup.add(ring1);

    const ring2 = new THREE.Mesh(ringGeo, ringMat);
    ring2.rotation.x = Math.PI * 0.5;
    patchGroup.add(ring2);

    // Destination marker — thin horizontal plane at bottom of chamber
    // Represents "AUTHORIZED WRITE" — only lit green in verified mode
    const destGeo = new THREE.BoxGeometry(3.6, 0.04, 2.0);
    const destMat = new THREE.MeshStandardMaterial({
      color: 0x064e3b,
      emissive: 0x059669,
      emissiveIntensity: 0.0,
      roughness: 0.3,
      metalness: 0.8,
    });
    const destMesh = new THREE.Mesh(destGeo, destMat);
    destMesh.position.set(0, endY + 0.6, 0);
    const destEdges = new THREE.LineSegments(
      new THREE.EdgesGeometry(destGeo),
      new THREE.LineBasicMaterial({ color: 0x065f46, transparent: true, opacity: 0.0 })
    );
    destMesh.add(destEdges);
    chamberGroup.add(destMesh);

    // 6. Reduced Data Sparks (18 instead of 35)
    const sparkCount = 18;
    const sparkGeo = new THREE.BufferGeometry();
    const sparkPositions = new Float32Array(sparkCount * 3);
    for (let i = 0; i < sparkCount; i++) {
      sparkPositions[i * 3]     = (Math.random() - 0.5) * 2.4;
      sparkPositions[i * 3 + 1] = (Math.random() - 0.5) * 6.4;
      sparkPositions[i * 3 + 2] = (Math.random() - 0.5) * 1.6;
    }
    sparkGeo.setAttribute("position", new THREE.BufferAttribute(sparkPositions, 3));
    const sparkPoints = new THREE.Points(
      sparkGeo,
      new THREE.PointsMaterial({
        color: 0x34d399,
        size: 0.038,
        transparent: true,
        opacity: 0.50,
      })
    );
    chamberGroup.add(sparkPoints);

    // --- MOUSE PARALLAX TRACKING ---
    let mouseX = 0;
    let mouseY = 0;
    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 1.6;
      mouseY = -((e.clientY - rect.top) / rect.height - 0.5) * 1.0;
    };
    container.addEventListener("mousemove", handleMouseMove);

    // --- RESIZE OBSERVER ---
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    setIsLoaded(true);

    // --- ANIMATION LOOP ---
    let frameId: number;
    let tAcc = 0;           // time accumulator — avoids Date.now() every frame
    let frameCount = 0;     // for every-other-frame optimizations
    // startY, endY, failHaltY are declared above (before destMesh)

    // Gate Y positions for dwell logic — patch pauses near each gate
    const gateYs = GATES.map((g) => g.y);

    // Convert tAcc (0..1 within a cycle) → actual Y with gate dwells
    // The patch lingers ~12% of cycle time near each gate
    const CYCLE_DURATION = 1.0; // 1 full cycle = startY → endY
    const DWELL_FRACTION = 0.10; // fraction of cycle spent pausing at each gate
    const travelFraction = CYCLE_DURATION - GATES.length * DWELL_FRACTION; // ~0.5

    function patchYFromT(t: number): number {
      // t ∈ [0, 1) — maps to Y with gate dwells at each verification gate
      const segments = GATES.length + 1; // gaps between start, each gate, and end
      const segSize = travelFraction / segments;

      let elapsed = 0;
      let y = startY;

      for (let i = 0; i <= GATES.length; i++) {
        const targetY = i < GATES.length ? gateYs[i] : endY;
        const segEnd = elapsed + segSize;

        if (t < segEnd) {
          // Travelling in this segment
          const segT = (t - elapsed) / segSize;
          const prevY = i === 0 ? startY : (i <= GATES.length ? gateYs[i - 1] : gateYs[GATES.length - 1]);
          y = prevY + (targetY - prevY) * Math.min(segT, 1.0);
          return y;
        }
        elapsed = segEnd;

        // Dwell at gate i (if there is one)
        if (i < GATES.length) {
          const dwellEnd = elapsed + DWELL_FRACTION;
          if (t < dwellEnd) {
            return gateYs[i] + Math.sin((t - elapsed) * Math.PI * 8) * 0.018;
          }
          elapsed = dwellEnd;
          y = gateYs[i];
        }
      }
      return endY;
    }

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      frameCount++;

      tAcc += 0.016; // ~60fps tick

      // Smooth Camera Parallax Orbit
      const targetCamX = initialCamPos.x + mouseX;
      const targetCamY = initialCamPos.y + mouseY;
      camera.position.x += (targetCamX - camera.position.x) * 0.06;
      camera.position.y += (targetCamY - camera.position.y) * 0.06;
      camera.lookAt(0, -0.5, 0);

      // Subtle Chamber Breathing (use tAcc instead of Date.now())
      chamberGroup.rotation.y = Math.sin(tAcc * 0.3) * 0.10;

      // Gyroscope Ring Rotations
      patchCore.rotation.x += 0.018;
      patchCore.rotation.y += 0.022;
      ring1.rotation.y += 0.030;
      ring2.rotation.x += 0.030;

      // Particle Drift — every other frame for performance
      if (frameCount % 2 === 0) {
        const posArr = sparkGeo.attributes.position.array as Float32Array;
        for (let i = 0; i < sparkCount; i++) {
          posArr[i * 3 + 1] -= 0.012;
          if (posArr[i * 3 + 1] < -3.4) posArr[i * 3 + 1] = 3.4;
        }
        sparkGeo.attributes.position.needsUpdate = true;
      }

      if (!prefersReducedMotion) {
        const curMode = modeRef.current;

        if (curMode === "verified") {
          // Patch travels at 0.003/tick — full cycle in ~5.5s at 60fps
          // (tAcc increments by 0.016 in the outer block)
          const cycleT = (tAcc * 0.003 * 3) % 1.0;
          const curY = patchYFromT(cycleT);
          const isAtDestination = curY <= endY + 1.0;

          patchGroup.position.set(
            Math.sin(cycleT * Math.PI * 1.5) * 0.04,
            curY,
            Math.cos(cycleT * Math.PI * 1.5) * 0.03
          );
          patchPointLight.position.set(0, curY, 0.5);

          // Verified styling
          patchCoreMat.color.setHex(0x34d399);
          patchCoreMat.emissive.setHex(0x059669);
          ringMat.color.setHex(0x6ee7b7);
          patchPointLight.color.setHex(0x34d399);
          barrierPlateMat.opacity = 0.0;
          (barrierLattice.material as THREE.LineBasicMaterial).opacity = 0.0;

          // Destination marker — lights up green when patch arrives
          destMat.emissiveIntensity = isAtDestination ? 0.6 : 0.0;
          (destEdges.material as THREE.LineBasicMaterial).opacity = isAtDestination ? 0.8 : 0.0;

          gateObjects.forEach((go) => {
            const hasPassed = curY <= go.y;
            const isNear = Math.abs(curY - go.y) < 0.6;

            if (hasPassed) {
              (go.aperture.material as THREE.MeshStandardMaterial).emissive.setHex(0x059669);
              (go.aperture.material as THREE.MeshStandardMaterial).emissiveIntensity = isNear ? 2.4 : 0.9;
              (go.border.material as THREE.LineBasicMaterial).color.setHex(0x34d399);
              go.glowLight.intensity = isNear ? 2.5 : 0.5;
              go.glowLight.color.setHex(0x34d399);
            } else {
              (go.aperture.material as THREE.MeshStandardMaterial).emissive.setHex(0x09090b);
              (go.aperture.material as THREE.MeshStandardMaterial).emissiveIntensity = 0.08;
              (go.border.material as THREE.LineBasicMaterial).color.setHex(0x141420);
              go.glowLight.intensity = 0.0;
            }
          });
        } else {
          // Unsafe Blocked Mode — enters, passes 2 gates, halts at gate 3
          // Cycle: 0→halt, pause, reset, repeat
          const blockedCycleDuration = 1.6;
          const blockedT = (tAcc * 0.003 * 3) % blockedCycleDuration;
          const entryFraction = 0.5; // first half = travelling
          let curY: number;
          let isAtBarrier = false;

          if (blockedT < entryFraction) {
            // Travelling from start to failHalt
            curY = startY + (failHaltY - startY) * (blockedT / entryFraction);
            isAtBarrier = false;
          } else {
            // Hovering at barrier
            curY = failHaltY + Math.sin(tAcc * 12) * 0.016;
            isAtBarrier = true;
          }

          patchGroup.position.set(0, curY, 0);
          patchPointLight.position.set(0, curY, 0.5);

          // Destination stays dark in blocked mode
          destMat.emissiveIntensity = 0.0;
          (destEdges.material as THREE.LineBasicMaterial).opacity = 0.0;

          if (isAtBarrier) {
            patchCoreMat.color.setHex(0xf87171);
            patchCoreMat.emissive.setHex(0xb91c1c);
            ringMat.color.setHex(0xfca5a5);
            patchPointLight.color.setHex(0xf87171);
            barrierPlateMat.opacity = 0.88;
            (barrierLattice.material as THREE.LineBasicMaterial).opacity = 1.0;
          } else {
            patchCoreMat.color.setHex(0xfbbf24);
            patchCoreMat.emissive.setHex(0xb45309);
            ringMat.color.setHex(0xfde68a);
            patchPointLight.color.setHex(0xfbbf24);
            barrierPlateMat.opacity = 0.0;
            (barrierLattice.material as THREE.LineBasicMaterial).opacity = 0.0;
          }

          gateObjects.forEach((go, idx) => {
            const hasPassed = curY <= go.y;
            if (idx < 2) {
              if (hasPassed) {
                (go.aperture.material as THREE.MeshStandardMaterial).emissive.setHex(0x059669);
                (go.aperture.material as THREE.MeshStandardMaterial).emissiveIntensity = 0.7;
                (go.border.material as THREE.LineBasicMaterial).color.setHex(0x34d399);
                go.glowLight.intensity = 0.5;
                go.glowLight.color.setHex(0x34d399);
              } else {
                (go.aperture.material as THREE.MeshStandardMaterial).emissive.setHex(0x09090b);
                (go.aperture.material as THREE.MeshStandardMaterial).emissiveIntensity = 0.08;
                (go.border.material as THREE.LineBasicMaterial).color.setHex(0x141420);
                go.glowLight.intensity = 0.0;
              }
            } else if (idx === 2) {
              if (isAtBarrier) {
                (go.aperture.material as THREE.MeshStandardMaterial).emissive.setHex(0xb91c1c);
                (go.aperture.material as THREE.MeshStandardMaterial).emissiveIntensity = 2.4;
                (go.border.material as THREE.LineBasicMaterial).color.setHex(0xf87171);
                go.glowLight.intensity = 2.6;
                go.glowLight.color.setHex(0xf87171);
              } else {
                (go.aperture.material as THREE.MeshStandardMaterial).emissive.setHex(0x09090b);
                (go.aperture.material as THREE.MeshStandardMaterial).emissiveIntensity = 0.08;
                (go.border.material as THREE.LineBasicMaterial).color.setHex(0x141420);
                go.glowLight.intensity = 0.0;
              }
            } else {
              (go.aperture.material as THREE.MeshStandardMaterial).emissive.setHex(0x09090b);
              (go.border.material as THREE.LineBasicMaterial).color.setHex(0x141420);
              go.glowLight.intensity = 0.0;
            }
          });
        }
      }

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
      container.removeEventListener("mousemove", handleMouseMove);
      renderer.dispose();
      pylonGeo.dispose();
      pylonMat.dispose();
      pylonEdgeGeo.dispose();
      girderGeo.dispose();
      girderMat.dispose();
      deckGeo.dispose();
      deckEdgeGeo.dispose();
      apertureGeo.dispose();
      patchCoreGeo.dispose();
      patchCoreMat.dispose();
      ringGeo.dispose();
      ringMat.dispose();
      sparkGeo.dispose();
      barrierPlateGeo.dispose();
      barrierPlateMat.dispose();
      destGeo.dispose();
      destMat.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden select-none"
      style={{ minHeight: "680px", height: "100%" }}
      aria-label="3D Security Verification Chamber"
    >
      {/* ── 3D WEBGL CANVAS ── */}
      {webglSupported ? (
        <canvas
          ref={canvasRef}
          className={`absolute inset-0 w-full h-full transition-opacity duration-500 ${
            isLoaded ? "opacity-100" : "opacity-0"
          }`}
        />
      ) : (
        /* Accessible 2D Fallback */
        <div className="absolute inset-0 p-8 flex flex-col justify-center items-center text-center space-y-5 bg-zinc-950">
          <div className="p-6 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 max-w-md text-left space-y-3 font-mono text-sm">
            <div className="text-sm font-bold text-emerald-400 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5" />
              <span>VERIFICATION BOUNDARY</span>
            </div>
            <div className="space-y-2 text-xs text-zinc-400">
              <div>01. AST Tree-sitter Grammar Parse (Valid)</div>
              <div>02. gVisor 0-Egress Sandbox (Isolated)</div>
              <div>03. 48/48 Regression Tests (Passed)</div>
              <div>04. Deterministic Severity Policy (High/Critical)</div>
              <div>05. RFC 8032 Ed25519 Cryptographic Proof (Signed)</div>
            </div>
          </div>
        </div>
      )}

      {/* ── FLOATING MODE TOGGLE — top-right overlay ── */}
      <div className="absolute top-4 right-4 z-10">
        <div className="inline-flex p-0.5 rounded-lg bg-zinc-950/70 backdrop-blur-sm border border-zinc-800/60 text-xs font-mono">
          <button
            onClick={() => setMode("verified")}
            className={`px-3 py-1.5 rounded-md transition-all duration-150 flex items-center gap-1.5 font-semibold ${
              mode === "verified"
                ? "bg-emerald-950/80 text-emerald-300 border border-emerald-800/60"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
            aria-pressed={mode === "verified"}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            Verified
          </button>
          <button
            onClick={() => setMode("blocked")}
            className={`px-3 py-1.5 rounded-md transition-all duration-150 flex items-center gap-1.5 font-semibold ${
              mode === "blocked"
                ? "bg-rose-950/80 text-rose-300 border border-rose-800/60"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
            aria-pressed={mode === "blocked"}
          >
            <XCircle className="w-3.5 h-3.5" />
            Blocked
          </button>
        </div>
      </div>

      {/* ── FLOATING STATUS PILL — bottom-left overlay ── */}
      <div className="absolute bottom-4 left-4 z-10">
        {mode === "verified" ? (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-zinc-950/70 backdrop-blur-sm border border-emerald-800/40 text-emerald-300 font-mono text-xs font-semibold">
            <Check className="w-3 h-3 text-emerald-400" />
            5/5 GATES · WRITE AUTHORIZED
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-zinc-950/70 backdrop-blur-sm border border-rose-800/40 text-rose-400 font-mono text-xs font-semibold">
            <X className="w-3 h-3 text-rose-400" />
            GATE 3 FAILED · WRITE BLOCKED
          </span>
        )}
      </div>

      {/* ── GATE LABELS — left-side HTML overlays, proportional to 3D gate Y positions ── */}
      {/* Gate positions in 3D: startY=3.8, endY=-4.0, total range=7.8 */}
      {/* Canvas height maps startY→top, endY→bottom */}
      <div className="absolute inset-0 z-10 pointer-events-none font-mono select-none hidden lg:block">
        {/* PATCH ENTRY — top */}
        <div className="absolute left-4" style={{ top: "5%" }}>
          <span className="text-[10px] uppercase tracking-[0.18em] text-zinc-700">PATCH</span>
        </div>

        {/* Gate labels — proportionally positioned to match 3D geometry */}
        {/* 3D range: startY=3.8 to endY=-4.0. Gate Y values mapped to % */}
        {GATES.map((gate, i) => {
          const totalRange = 3.8 - (-4.0); // 7.8
          const pct = ((3.8 - gate.y) / totalRange) * 80 + 5; // 5%→85% range
          const isFailGate = mode === "blocked" && i === 2;
          return (
            <div key={gate.id} className="absolute left-4" style={{ top: `${pct}%` }}>
              <span className={`text-[10px] uppercase tracking-[0.18em] ${
                isFailGate ? "text-rose-500/80" : "text-zinc-700"
              }`}>
                {gate.label}
              </span>
            </div>
          );
        })}

        {/* AUTH. WRITE — bottom, lights emerald when verified */}
        <div className="absolute left-4" style={{ top: "89%" }}>
          <span className={`text-[10px] uppercase tracking-[0.18em] transition-colors duration-700 ${
            mode === "verified" ? "text-emerald-500/70" : "text-zinc-800"
          }`}>
            AUTH. WRITE
          </span>
        </div>
      </div>
    </div>
  );
}
