/**
 * Utility functions for Interactive Depth Editor types
 */

import type {
  DepthPlane,
  DepthLayer,
  InteractiveDepthEditorConfig,
  DepthMapExport,
} from '../api/types';

/**
 * Generate a unique ID for depth planes and layers
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Create a default depth plane
 */
export function createDefaultPlane(
  name: string = 'New Plane',
  depthValue: number = 0.5
): DepthPlane {
  return {
    id: generateId(),
    name,
    depth_value: Math.max(0, Math.min(1, depthValue)),
    color: getDefaultPlaneColor(depthValue),
    visible: true,
    locked: false,
    points: [],
  };
}

/**
 * Get a default color for a plane based on its depth value
 * Uses a gradient from red (near) to blue (far)
 */
export function getDefaultPlaneColor(depthValue: number): string {
  const normalized = Math.max(0, Math.min(1, depthValue));
  const r = Math.round(255 * (1 - normalized));
  const b = Math.round(255 * normalized);
  return `#${r.toString(16).padStart(2, '0')}00${b.toString(16).padStart(2, '0')}`;
}

/**
 * Create a default depth layer
 */
export function createDefaultLayer(name: string = 'New Layer'): DepthLayer {
  return {
    id: generateId(),
    name,
    visible: true,
    locked: false,
    opacity: 1,
    blend_mode: 'normal',
    data: null,
  };
}

/**
 * Create a default editor configuration
 */
export function createDefaultConfig(
  width: number = 640,
  height: number = 480
): InteractiveDepthEditorConfig {
  return {
    width,
    height,
    layers: [createDefaultLayer('Base Layer')],
    planes: [],
    active_layer_id: null,
    active_plane_id: null,
  };
}

/**
 * Validate that a depth value is within the valid range
 */
export function isValidDepthValue(value: number): boolean {
  return typeof value === 'number' && !isNaN(value) && value >= 0 && value <= 1;
}

/**
 * Validate that an opacity value is within the valid range
 */
export function isValidOpacity(value: number): boolean {
  return typeof value === 'number' && !isNaN(value) && value >= 0 && value <= 1;
}

/**
 * Validate that a point is within normalized coordinates
 */
export function isValidPoint(point: { x: number; y: number }): boolean {
  return (
    typeof point.x === 'number' &&
    typeof point.y === 'number' &&
    !isNaN(point.x) &&
    !isNaN(point.y) &&
    point.x >= 0 &&
    point.x <= 1 &&
    point.y >= 0 &&
    point.y <= 1
  );
}

/**
 * Validate all points in a plane
 */
export function areValidPoints(points: { x: number; y: number }[]): boolean {
  return Array.isArray(points) && points.every(isValidPoint);
}

/**
 * Validate a blend mode
 */
export function isValidBlendMode(mode: string): mode is DepthLayer['blend_mode'] {
  return ['normal', 'multiply', 'screen', 'overlay'].includes(mode);
}

/**
 * Validate a depth plane object
 */
export function isValidPlane(plane: unknown): plane is DepthPlane {
  if (typeof plane !== 'object' || plane === null) return false;

  const p = plane as Partial<DepthPlane>;

  return (
    typeof p.id === 'string' &&
    typeof p.name === 'string' &&
    isValidDepthValue(p.depth_value as number) &&
    typeof p.color === 'string' &&
    typeof p.visible === 'boolean' &&
    typeof p.locked === 'boolean' &&
    Array.isArray(p.points)
  );
}

/**
 * Validate a depth layer object
 */
export function isValidLayer(layer: unknown): layer is DepthLayer {
  if (typeof layer !== 'object' || layer === null) return false;

  const l = layer as Partial<DepthLayer>;

  return (
    typeof l.id === 'string' &&
    typeof l.name === 'string' &&
    typeof l.visible === 'boolean' &&
    typeof l.locked === 'boolean' &&
    isValidOpacity(l.opacity as number) &&
    isValidBlendMode(l.blend_mode as string)
  );
}

/**
 * Clamp a depth value to valid range
 */
export function clampDepthValue(value: number): number {
  return Math.max(0, Math.min(1, value));
}

/**
 * Clamp an opacity value to valid range
 */
export function clampOpacity(value: number): number {
  return Math.max(0, Math.min(1, value));
}

/**
 * Merge multiple depth planes into a single sorted array by depth
 */
export function sortPlanesByDepth(planes: DepthPlane[]): DepthPlane[] {
  return [...planes].sort((a, b) => a.depth_value - b.depth_value);
}

/**
 * Get visible planes only
 */
export function getVisiblePlanes(planes: DepthPlane[]): DepthPlane[] {
  return planes.filter((plane) => plane.visible);
}

/**
 * Get visible layers only
 */
export function getVisibleLayers(layers: DepthLayer[]): DepthLayer[] {
  return layers.filter((layer) => layer.visible);
}

/**
 * Get unlocked layers only
 */
export function getUnlockedLayers(layers: DepthLayer[]): DepthLayer[] {
  return layers.filter((layer) => !layer.locked);
}

/**
 * Find a plane by ID
 */
export function findPlaneById(planes: DepthPlane[], id: string): DepthPlane | undefined {
  return planes.find((plane) => plane.id === id);
}

/**
 * Find a layer by ID
 */
export function findLayerById(layers: DepthLayer[], id: string): DepthLayer | undefined {
  return layers.find((layer) => layer.id === id);
}

/**
 * Update a plane in the array
 */
export function updatePlane(
  planes: DepthPlane[],
  id: string,
  updates: Partial<DepthPlane>
): DepthPlane[] {
  return planes.map((plane) =>
    plane.id === id ? { ...plane, ...updates } : plane
  );
}

/**
 * Update a layer in the array
 */
export function updateLayer(
  layers: DepthLayer[],
  id: string,
  updates: Partial<DepthLayer>
): DepthLayer[] {
  return layers.map((layer) =>
    layer.id === id ? { ...layer, ...updates } : layer
  );
}

/**
 * Remove a plane from the array
 */
export function removePlane(planes: DepthPlane[], id: string): DepthPlane[] {
  return planes.filter((plane) => plane.id !== id);
}

/**
 * Remove a layer from the array
 */
export function removeLayer(layers: DepthLayer[], id: string): DepthLayer[] {
  return layers.filter((layer) => layer.id !== id);
}

/**
 * Create a depth map export from config
 */
export function createDepthMapExport(
  config: InteractiveDepthEditorConfig,
  data: string
): DepthMapExport {
  return {
    width: config.width,
    height: config.height,
    data,
    planes: config.planes,
  };
}
