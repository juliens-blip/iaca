"use client";

import { useCallback, useMemo, useRef, useState, type CSSProperties } from "react";

export interface MindMapNode {
  id: string;
  label: string;
  x: number;
  y: number;
  description?: string;
  color?: string;
  size?: "sm" | "md" | "lg";
}

export interface MindMapLink {
  id?: string;
  source: string;
  target: string;
  label?: string;
  color?: string;
  dashed?: boolean;
  thickness?: number;
}

export interface MindMapData {
  nodes: MindMapNode[];
  links: MindMapLink[];
}

export interface GeminiMindMapBranch {
  nom: string;
  sous_branches?: string[];
  details?: string;
}

export interface GeminiMindMapData {
  centre: string;
  branches: GeminiMindMapBranch[];
}

type CoordinateMode = "percent" | "pixel";

interface MindMapProps {
  data: MindMapData;
  title?: string;
  className?: string;
  height?: number;
  coordinateMode?: CoordinateMode;
  showControls?: boolean;
  enablePanZoom?: boolean;
  initialZoom?: number;
  minZoom?: number;
  maxZoom?: number;
  onNodeClick?: (node: MindMapNode) => void;
}

interface PanState {
  pointerId: number;
  startX: number;
  startY: number;
  originX: number;
  originY: number;
}

type PositionedNode = MindMapNode & { position: { x: number; y: number } };

const CANVAS_WIDTH = 1000;
const CANVAS_HEIGHT = 700;

const NODE_THEME_CLASSES = [
  "border-blue-400/40 bg-blue-500/10 text-blue-100 shadow-blue-500/20",
  "border-violet-400/40 bg-violet-500/10 text-violet-100 shadow-violet-500/20",
  "border-emerald-400/40 bg-emerald-500/10 text-emerald-100 shadow-emerald-500/20",
  "border-amber-400/40 bg-amber-500/10 text-amber-100 shadow-amber-500/20",
  "border-cyan-400/40 bg-cyan-500/10 text-cyan-100 shadow-cyan-500/20",
  "border-rose-400/40 bg-rose-500/10 text-rose-100 shadow-rose-500/20",
];

const NODE_SIZE_CLASSES: Record<NonNullable<MindMapNode["size"]>, string> = {
  sm: "min-w-[110px] max-w-[160px] px-3 py-2 text-xs",
  md: "min-w-[140px] max-w-[200px] px-4 py-2.5 text-sm",
  lg: "min-w-[170px] max-w-[230px] px-5 py-3 text-sm",
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function normalizeId(value: string): string {
  const normalized = value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-");
  return normalized.replace(/^-+|-+$/g, "") || "node";
}

function createUniqueId(value: string, usedIds: Set<string>): string {
  const baseId = normalizeId(value);
  let candidateId = baseId;
  let counter = 1;

  while (usedIds.has(candidateId)) {
    candidateId = `${baseId}-${counter}`;
    counter += 1;
  }

  usedIds.add(candidateId);
  return candidateId;
}

function resolveNodePosition(node: MindMapNode, coordinateMode: CoordinateMode): { x: number; y: number } {
  if (coordinateMode === "pixel") {
    return {
      x: clamp(node.x, 24, CANVAS_WIDTH - 24),
      y: clamp(node.y, 24, CANVAS_HEIGHT - 24),
    };
  }

  return {
    x: clamp((node.x / 100) * CANVAS_WIDTH, 24, CANVAS_WIDTH - 24),
    y: clamp((node.y / 100) * CANVAS_HEIGHT, 24, CANVAS_HEIGHT - 24),
  };
}

function getNodeStyle(index: number, node: PositionedNode, isSelected: boolean, isConnected: boolean): CSSProperties {
  const style: CSSProperties = {
    left: `${node.position.x}px`,
    top: `${node.position.y}px`,
    opacity: isConnected ? 1 : 0.3,
  };

  if (!node.color) {
    return style;
  }

  style.borderColor = node.color;
  style.backgroundColor = "rgba(15, 23, 42, 0.95)";
  style.color = "#e2e8f0";
  style.boxShadow = isSelected
    ? `0 0 0 1px ${node.color}, 0 0 0 8px ${node.color}33, 0 14px 30px ${node.color}33`
    : `0 10px 24px ${node.color}26`;

  return style;
}

function getNodeClass(index: number, node: PositionedNode, isSelected: boolean, isConnected: boolean): string {
  const sizeClass = NODE_SIZE_CLASSES[node.size ?? "md"];
  const themeClass = node.color ? "" : NODE_THEME_CLASSES[index % NODE_THEME_CLASSES.length];

  return [
    "absolute -translate-x-1/2 -translate-y-1/2 rounded-2xl border text-left shadow-xl backdrop-blur-sm",
    "transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-300/45",
    sizeClass,
    themeClass,
    isSelected ? "scale-105 ring-2 ring-blue-300/40" : "hover:scale-105",
    isConnected ? "" : "saturate-0",
  ]
    .filter(Boolean)
    .join(" ");
}

export function convertGeminiMindMapToGraph(mindMap: GeminiMindMapData): MindMapData {
  const nodes: MindMapNode[] = [];
  const links: MindMapLink[] = [];
  const usedIds = new Set<string>();

  const centerLabel = mindMap.centre?.trim() || "Sujet";
  const centerId = createUniqueId(centerLabel, usedIds);
  nodes.push({
    id: centerId,
    label: centerLabel,
    x: 50,
    y: 50,
    size: "lg",
    color: "#38bdf8",
  });

  const branchCount = Math.max(mindMap.branches.length, 1);
  const branchPalette = ["#a78bfa", "#34d399", "#f59e0b", "#f472b6", "#22d3ee", "#60a5fa"];

  mindMap.branches.forEach((branch, branchIndex) => {
    const branchLabel = branch.nom?.trim() || `Branche ${branchIndex + 1}`;
    const branchId = createUniqueId(branchLabel, usedIds);
    const branchAngle = (Math.PI * 2 * branchIndex) / branchCount - Math.PI / 2;
    const branchX = clamp(50 + 30 * Math.cos(branchAngle), 10, 90);
    const branchY = clamp(50 + 30 * Math.sin(branchAngle), 10, 90);
    const branchColor = branchPalette[branchIndex % branchPalette.length];

    nodes.push({
      id: branchId,
      label: branchLabel,
      x: branchX,
      y: branchY,
      size: "md",
      color: branchColor,
      description: branch.details,
    });

    links.push({
      id: `${centerId}-${branchId}`,
      source: centerId,
      target: branchId,
      thickness: 2.2,
      color: `${branchColor}88`,
    });

    const subBranches = branch.sous_branches ?? [];
    const subCount = subBranches.length;

    subBranches.forEach((subBranch, subIndex) => {
      const subLabel = subBranch.trim();
      if (!subLabel) return;

      const offset = subCount > 1 ? subIndex - (subCount - 1) / 2 : 0;
      const subAngle = branchAngle + offset * 0.42;
      const subX = clamp(branchX + 13 * Math.cos(subAngle), 6, 94);
      const subY = clamp(branchY + 13 * Math.sin(subAngle), 6, 94);
      const subId = createUniqueId(`${branchId}-${subLabel}`, usedIds);

      nodes.push({
        id: subId,
        label: subLabel,
        x: subX,
        y: subY,
        size: "sm",
        color: branchColor,
      });

      links.push({
        id: `${branchId}-${subId}`,
        source: branchId,
        target: subId,
        dashed: true,
        thickness: 1.6,
        color: `${branchColor}70`,
      });
    });
  });

  return { nodes, links };
}

export default function MindMap({
  data,
  title = "Mind Map",
  className,
  height = 560,
  coordinateMode = "percent",
  showControls = true,
  enablePanZoom = true,
  initialZoom = 1,
  minZoom = 0.55,
  maxZoom = 2.3,
  onNodeClick,
}: MindMapProps) {
  const defaultScale = clamp(initialZoom, minZoom, maxZoom);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [view, setView] = useState({ x: 0, y: 0, scale: defaultScale });
  const [isPanning, setIsPanning] = useState(false);
  const panStateRef = useRef<PanState | null>(null);

  const positionedNodes = useMemo<PositionedNode[]>(() => {
    return data.nodes.map((node) => ({
      ...node,
      position: resolveNodePosition(node, coordinateMode),
    }));
  }, [data.nodes, coordinateMode]);

  const nodeById = useMemo(() => {
    return new Map(positionedNodes.map((node) => [node.id, node]));
  }, [positionedNodes]);

  const validLinks = useMemo(() => {
    return data.links.filter((link) => nodeById.has(link.source) && nodeById.has(link.target));
  }, [data.links, nodeById]);

  const connectedNodeIds = useMemo(() => {
    const ids = new Set<string>();
    if (!selectedNodeId) return ids;

    validLinks.forEach((link) => {
      if (link.source === selectedNodeId) ids.add(link.target);
      if (link.target === selectedNodeId) ids.add(link.source);
    });

    return ids;
  }, [selectedNodeId, validLinks]);

  const selectedNode = selectedNodeId ? nodeById.get(selectedNodeId) ?? null : null;
  const wrapperClassName = className ? `card ${className}` : "card";

  const adjustZoom = useCallback(
    (delta: number) => {
      setView((previous) => ({
        ...previous,
        scale: clamp(previous.scale + delta, minZoom, maxZoom),
      }));
    },
    [maxZoom, minZoom]
  );

  const resetView = useCallback(() => {
    setView({ x: 0, y: 0, scale: clamp(initialZoom, minZoom, maxZoom) });
  }, [initialZoom, maxZoom, minZoom]);

  const handleWheel = useCallback(
    (event: React.WheelEvent<HTMLDivElement>) => {
      if (!enablePanZoom) return;
      event.preventDefault();

      const bounds = event.currentTarget.getBoundingClientRect();
      const cursorX = event.clientX - bounds.left;
      const cursorY = event.clientY - bounds.top;
      const delta = event.deltaY < 0 ? 0.12 : -0.12;

      setView((previous) => {
        const nextScale = clamp(previous.scale + delta, minZoom, maxZoom);
        if (nextScale === previous.scale) return previous;

        const worldX = (cursorX - previous.x) / previous.scale;
        const worldY = (cursorY - previous.y) / previous.scale;

        return {
          x: cursorX - worldX * nextScale,
          y: cursorY - worldY * nextScale,
          scale: nextScale,
        };
      });
    },
    [enablePanZoom, maxZoom, minZoom]
  );

  const handlePointerDown = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (!enablePanZoom || event.button !== 0) return;

      panStateRef.current = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        originX: view.x,
        originY: view.y,
      };
      setIsPanning(true);
      event.currentTarget.setPointerCapture(event.pointerId);
    },
    [enablePanZoom, view.x, view.y]
  );

  const handlePointerMove = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    const panState = panStateRef.current;
    if (!panState || panState.pointerId !== event.pointerId) return;

    const deltaX = event.clientX - panState.startX;
    const deltaY = event.clientY - panState.startY;

    setView((previous) => ({
      ...previous,
      x: panState.originX + deltaX,
      y: panState.originY + deltaY,
    }));
  }, []);

  const finishPan = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    const panState = panStateRef.current;
    if (!panState || panState.pointerId !== event.pointerId) return;

    panStateRef.current = null;
    setIsPanning(false);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }, []);

  if (positionedNodes.length === 0) {
    return (
      <div className={wrapperClassName}>
        <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
        <p className="mt-2 text-sm text-slate-400">
          Aucune donnee a afficher. Fournissez au moins un noeud dans `data.nodes`.
        </p>
      </div>
    );
  }

  return (
    <section className={wrapperClassName}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
          <p className="text-xs text-slate-400">
            Cliquez un noeud pour voir ses connexions. Glisser + molette pour naviguer.
          </p>
        </div>
        {showControls && enablePanZoom && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => adjustZoom(-0.15)}
              className="btn-secondary px-3 py-1.5 text-sm"
              aria-label="Zoom out"
            >
              -
            </button>
            <button
              type="button"
              onClick={() => adjustZoom(0.15)}
              className="btn-secondary px-3 py-1.5 text-sm"
              aria-label="Zoom in"
            >
              +
            </button>
            <button
              type="button"
              onClick={resetView}
              className="btn-ghost px-3 py-1.5 text-sm"
            >
              Reset
            </button>
          </div>
        )}
      </div>

      <div
        className="relative overflow-hidden rounded-xl border border-slate-700/60 bg-slate-950/70"
        style={{ height: `${height}px` }}
      >
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.20),transparent_50%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(148,163,184,0.10)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.10)_1px,transparent_1px)] [background-size:48px_48px]" />

        <div
          className={[
            "absolute inset-0 touch-none",
            enablePanZoom ? (isPanning ? "cursor-grabbing" : "cursor-grab") : "cursor-default",
          ].join(" ")}
          onWheel={handleWheel}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={finishPan}
          onPointerCancel={finishPan}
          onDoubleClick={() => setSelectedNodeId(null)}
        >
          <div
            className="absolute left-1/2 top-1/2 origin-top-left"
            style={{
              width: `${CANVAS_WIDTH}px`,
              height: `${CANVAS_HEIGHT}px`,
              transform: `translate(-50%, -50%) translate(${view.x}px, ${view.y}px) scale(${view.scale})`,
              transition: isPanning ? "none" : "transform 120ms ease-out",
            }}
          >
            <svg
              className="absolute inset-0 h-full w-full pointer-events-none"
              viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`}
              aria-hidden="true"
            >
              {validLinks.map((link, index) => {
                const sourceNode = nodeById.get(link.source);
                const targetNode = nodeById.get(link.target);
                if (!sourceNode || !targetNode) return null;

                const isSelectedLink =
                  selectedNodeId !== null &&
                  (link.source === selectedNodeId || link.target === selectedNodeId);
                const opacity = selectedNodeId ? (isSelectedLink ? 0.95 : 0.2) : 0.7;
                const strokeWidth = link.thickness ?? (isSelectedLink ? 2.6 : 1.9);

                return (
                  <g key={link.id ?? `${link.source}-${link.target}-${index}`}>
                    <line
                      x1={sourceNode.position.x}
                      y1={sourceNode.position.y}
                      x2={targetNode.position.x}
                      y2={targetNode.position.y}
                      stroke={link.color ?? "rgba(148, 163, 184, 0.7)"}
                      strokeWidth={strokeWidth}
                      strokeLinecap="round"
                      strokeDasharray={link.dashed ? "7 6" : undefined}
                      opacity={opacity}
                    />
                    {link.label && (
                      <text
                        x={(sourceNode.position.x + targetNode.position.x) / 2}
                        y={(sourceNode.position.y + targetNode.position.y) / 2}
                        fill="rgba(226, 232, 240, 0.9)"
                        fontSize="11"
                        textAnchor="middle"
                        dominantBaseline="middle"
                      >
                        {link.label}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>

            {positionedNodes.map((node, index) => {
              const isSelected = selectedNodeId === node.id;
              const isConnected = !selectedNodeId || isSelected || connectedNodeIds.has(node.id);

              return (
                <button
                  key={node.id}
                  type="button"
                  className={getNodeClass(index, node, isSelected, isConnected)}
                  style={getNodeStyle(index, node, isSelected, isConnected)}
                  onPointerDown={(event) => event.stopPropagation()}
                  onClick={() => {
                    setSelectedNodeId(node.id);
                    onNodeClick?.(node);
                  }}
                  aria-pressed={isSelected}
                  aria-label={`Noeud ${node.label}`}
                >
                  <p className="font-semibold leading-tight">{node.label}</p>
                  {isSelected && node.description && (
                    <p className="mt-1.5 text-[11px] leading-snug text-slate-300/90">
                      {node.description}
                    </p>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {selectedNode && (
        <div className="mt-4 rounded-xl border border-slate-700/60 bg-slate-900/70 p-4">
          <div className="flex items-center justify-between gap-3">
            <h4 className="text-sm font-semibold text-slate-100">{selectedNode.label}</h4>
            <span className="badge-blue">Noeud actif</span>
          </div>
          <p className="mt-2 text-sm text-slate-300">
            {selectedNode.description || "Aucune description disponible pour ce noeud."}
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Connexions directes: {connectedNodeIds.size}
          </p>
        </div>
      )}
    </section>
  );
}
