import { describe, it, expect, beforeEach } from 'vitest';
import {
  generateId,
  createDefaultPlane,
  getDefaultPlaneColor,
  createDefaultLayer,
  createDefaultConfig,
  isValidDepthValue,
  isValidOpacity,
  isValidPoint,
  areValidPoints,
  isValidBlendMode,
  isValidPlane,
  isValidLayer,
  clampDepthValue,
  clampOpacity,
  sortPlanesByDepth,
  getVisiblePlanes,
  getVisibleLayers,
  getUnlockedLayers,
  findPlaneById,
  findLayerById,
  updatePlane,
  updateLayer,
  removePlane,
  removeLayer,
  createDepthMapExport,
} from '../depthEditorUtils';
import type { DepthPlane, DepthLayer, InteractiveDepthEditorConfig } from '../../api/types';

describe('depthEditorUtils', () => {
  // ============================================
  // generateId Tests
  // ============================================
  describe('generateId', () => {
    it('should generate a unique ID', () => {
      const id1 = generateId();
      const id2 = generateId();

      expect(id1).not.toBe(id2);
      expect(typeof id1).toBe('string');
      expect(id1.length).toBeGreaterThan(0);
    });

    it('should generate IDs that start with a timestamp', () => {
      const id = generateId();
      const timestamp = id.split('-')[0];

      expect(Number(timestamp)).toBeGreaterThan(0);
    });

    it('should generate multiple unique IDs', () => {
      const ids = new Set<string>();
      for (let i = 0; i < 100; i++) {
        ids.add(generateId());
      }

      expect(ids.size).toBe(100);
    });
  });

  // ============================================
  // createDefaultPlane Tests
  // ============================================
  describe('createDefaultPlane', () => {
    it('should create a plane with default values', () => {
      const plane = createDefaultPlane();

      expect(plane.name).toBe('New Plane');
      expect(plane.depth_value).toBe(0.5);
      expect(plane.visible).toBe(true);
      expect(plane.locked).toBe(false);
      expect(plane.points).toEqual([]);
    });

    it('should create a plane with custom name', () => {
      const plane = createDefaultPlane('Custom Plane');

      expect(plane.name).toBe('Custom Plane');
    });

    it('should create a plane with custom depth value', () => {
      const plane = createDefaultPlane('Deep', 0.8);

      expect(plane.depth_value).toBe(0.8);
    });

    it('should clamp depth value to valid range', () => {
      const negativePlane = createDefaultPlane('Negative', -0.5);
      const overOnePlane = createDefaultPlane('Over', 1.5);

      expect(negativePlane.depth_value).toBe(0);
      expect(overOnePlane.depth_value).toBe(1);
    });

    it('should assign different colors based on depth value', () => {
      const nearPlane = createDefaultPlane('Near', 0);
      const farPlane = createDefaultPlane('Far', 1);
      const midPlane = createDefaultPlane('Mid', 0.5);

      expect(nearPlane.color).toBe('#ff0000');
      expect(farPlane.color).toBe('#0000ff');
      expect(midPlane.color).toBe('#800080');
    });
  });

  // ============================================
  // getDefaultPlaneColor Tests
  // ============================================
  describe('getDefaultPlaneColor', () => {
    it('should return red for depth 0 (near)', () => {
      expect(getDefaultPlaneColor(0)).toBe('#ff0000');
    });

    it('should return blue for depth 1 (far)', () => {
      expect(getDefaultPlaneColor(1)).toBe('#0000ff');
    });

    it('should return purple for depth 0.5 (mid)', () => {
      expect(getDefaultPlaneColor(0.5)).toBe('#800080');
    });

    it('should clamp values outside range', () => {
      expect(getDefaultPlaneColor(-1)).toBe('#ff0000');
      expect(getDefaultPlaneColor(2)).toBe('#0000ff');
    });

    it('should return valid hex color format', () => {
      const color = getDefaultPlaneColor(0.3);
      expect(color).toMatch(/^#[0-9a-f]{6}$/);
    });
  });

  // ============================================
  // createDefaultLayer Tests
  // ============================================
  describe('createDefaultLayer', () => {
    it('should create a layer with default values', () => {
      const layer = createDefaultLayer();

      expect(layer.name).toBe('New Layer');
      expect(layer.visible).toBe(true);
      expect(layer.locked).toBe(false);
      expect(layer.opacity).toBe(1);
      expect(layer.blend_mode).toBe('normal');
      expect(layer.data).toBeNull();
    });

    it('should create a layer with custom name', () => {
      const layer = createDefaultLayer('Custom Layer');

      expect(layer.name).toBe('Custom Layer');
    });

    it('should generate unique IDs for each layer', () => {
      const layer1 = createDefaultLayer();
      const layer2 = createDefaultLayer();

      expect(layer1.id).not.toBe(layer2.id);
    });
  });

  // ============================================
  // createDefaultConfig Tests
  // ============================================
  describe('createDefaultConfig', () => {
    it('should create a config with default dimensions', () => {
      const config = createDefaultConfig();

      expect(config.width).toBe(640);
      expect(config.height).toBe(480);
      expect(config.layers).toHaveLength(1);
      expect(config.planes).toHaveLength(0);
      expect(config.active_layer_id).toBeNull();
      expect(config.active_plane_id).toBeNull();
    });

    it('should create a config with custom dimensions', () => {
      const config = createDefaultConfig(1920, 1080);

      expect(config.width).toBe(1920);
      expect(config.height).toBe(1080);
    });

    it('should include a base layer', () => {
      const config = createDefaultConfig();

      expect(config.layers[0].name).toBe('Base Layer');
    });
  });

  // ============================================
  // isValidDepthValue Tests
  // ============================================
  describe('isValidDepthValue', () => {
    it('should return true for valid depth values', () => {
      expect(isValidDepthValue(0)).toBe(true);
      expect(isValidDepthValue(0.5)).toBe(true);
      expect(isValidDepthValue(1)).toBe(true);
    });

    it('should return false for invalid depth values', () => {
      expect(isValidDepthValue(-0.1)).toBe(false);
      expect(isValidDepthValue(1.1)).toBe(false);
      expect(isValidDepthValue(NaN)).toBe(false);
      expect(isValidDepthValue(Infinity)).toBe(false);
    });

    it('should return false for non-numbers', () => {
      expect(isValidDepthValue('0.5' as unknown as number)).toBe(false);
      expect(isValidDepthValue(null as unknown as number)).toBe(false);
      expect(isValidDepthValue(undefined as unknown as number)).toBe(false);
    });
  });

  // ============================================
  // isValidOpacity Tests
  // ============================================
  describe('isValidOpacity', () => {
    it('should return true for valid opacity values', () => {
      expect(isValidOpacity(0)).toBe(true);
      expect(isValidOpacity(0.5)).toBe(true);
      expect(isValidOpacity(1)).toBe(true);
    });

    it('should return false for invalid opacity values', () => {
      expect(isValidOpacity(-0.1)).toBe(false);
      expect(isValidOpacity(1.1)).toBe(false);
      expect(isValidOpacity(NaN)).toBe(false);
    });
  });

  // ============================================
  // isValidPoint Tests
  // ============================================
  describe('isValidPoint', () => {
    it('should return true for valid points', () => {
      expect(isValidPoint({ x: 0, y: 0 })).toBe(true);
      expect(isValidPoint({ x: 0.5, y: 0.5 })).toBe(true);
      expect(isValidPoint({ x: 1, y: 1 })).toBe(true);
    });

    it('should return false for invalid points', () => {
      expect(isValidPoint({ x: -0.1, y: 0.5 })).toBe(false);
      expect(isValidPoint({ x: 0.5, y: 1.1 })).toBe(false);
      expect(isValidPoint({ x: NaN, y: 0.5 })).toBe(false);
    });

    it('should return false for non-numeric coordinates', () => {
      expect(isValidPoint({ x: '0.5' as unknown as number, y: 0.5 })).toBe(false);
      expect(isValidPoint({ x: null as unknown as number, y: 0.5 })).toBe(false);
    });
  });

  // ============================================
  // areValidPoints Tests
  // ============================================
  describe('areValidPoints', () => {
    it('should return true for empty array', () => {
      expect(areValidPoints([])).toBe(true);
    });

    it('should return true for array of valid points', () => {
      expect(
        areValidPoints([
          { x: 0, y: 0 },
          { x: 0.5, y: 0.5 },
          { x: 1, y: 1 },
        ])
      ).toBe(true);
    });

    it('should return false if any point is invalid', () => {
      expect(
        areValidPoints([
          { x: 0, y: 0 },
          { x: 1.5, y: 0.5 },
        ])
      ).toBe(false);
    });
  });

  // ============================================
  // isValidBlendMode Tests
  // ============================================
  describe('isValidBlendMode', () => {
    it('should return true for valid blend modes', () => {
      expect(isValidBlendMode('normal')).toBe(true);
      expect(isValidBlendMode('multiply')).toBe(true);
      expect(isValidBlendMode('screen')).toBe(true);
      expect(isValidBlendMode('overlay')).toBe(true);
    });

    it('should return false for invalid blend modes', () => {
      expect(isValidBlendMode('darken')).toBe(false);
      expect(isValidBlendMode('lighten')).toBe(false);
      expect(isValidBlendMode('')).toBe(false);
    });
  });

  // ============================================
  // isValidPlane Tests
  // ============================================
  describe('isValidPlane', () => {
    it('should return true for valid plane', () => {
      const plane: DepthPlane = {
        id: 'test',
        name: 'Test',
        depth_value: 0.5,
        color: '#ff0000',
        visible: true,
        locked: false,
        points: [],
      };

      expect(isValidPlane(plane)).toBe(true);
    });

    it('should return false for invalid planes', () => {
      expect(isValidPlane(null)).toBe(false);
      expect(isValidPlane({})).toBe(false);
      expect(isValidPlane({ id: 123 } as unknown as DepthPlane)).toBe(false);
    });

    it('should return false for plane with invalid depth_value', () => {
      const plane = {
        id: 'test',
        name: 'Test',
        depth_value: 1.5,
        color: '#ff0000',
        visible: true,
        locked: false,
        points: [],
      };

      expect(isValidPlane(plane)).toBe(false);
    });
  });

  // ============================================
  // isValidLayer Tests
  // ============================================
  describe('isValidLayer', () => {
    it('should return true for valid layer', () => {
      const layer: DepthLayer = {
        id: 'test',
        name: 'Test',
        visible: true,
        locked: false,
        opacity: 1,
        blend_mode: 'normal',
        data: null,
      };

      expect(isValidLayer(layer)).toBe(true);
    });

    it('should return false for invalid layers', () => {
      expect(isValidLayer(null)).toBe(false);
      expect(isValidLayer({})).toBe(false);
    });

    it('should return false for layer with invalid opacity', () => {
      const layer = {
        id: 'test',
        name: 'Test',
        visible: true,
        locked: false,
        opacity: 1.5,
        blend_mode: 'normal',
        data: null,
      };

      expect(isValidLayer(layer)).toBe(false);
    });

    it('should return false for layer with invalid blend_mode', () => {
      const layer = {
        id: 'test',
        name: 'Test',
        visible: true,
        locked: false,
        opacity: 1,
        blend_mode: 'invalid',
        data: null,
      };

      expect(isValidLayer(layer)).toBe(false);
    });
  });

  // ============================================
  // clampDepthValue Tests
  // ============================================
  describe('clampDepthValue', () => {
    it('should return value if within range', () => {
      expect(clampDepthValue(0.5)).toBe(0.5);
    });

    it('should clamp to 0 if below range', () => {
      expect(clampDepthValue(-0.5)).toBe(0);
    });

    it('should clamp to 1 if above range', () => {
      expect(clampDepthValue(1.5)).toBe(1);
    });
  });

  // ============================================
  // clampOpacity Tests
  // ============================================
  describe('clampOpacity', () => {
    it('should return value if within range', () => {
      expect(clampOpacity(0.7)).toBe(0.7);
    });

    it('should clamp to 0 if below range', () => {
      expect(clampOpacity(-0.3)).toBe(0);
    });

    it('should clamp to 1 if above range', () => {
      expect(clampOpacity(1.3)).toBe(1);
    });
  });

  // ============================================
  // sortPlanesByDepth Tests
  // ============================================
  describe('sortPlanesByDepth', () => {
    it('should sort planes by depth value ascending', () => {
      const planes: DepthPlane[] = [
        createDefaultPlane('Far', 0.8),
        createDefaultPlane('Near', 0.2),
        createDefaultPlane('Mid', 0.5),
      ];

      const sorted = sortPlanesByDepth(planes);

      expect(sorted[0].depth_value).toBe(0.2);
      expect(sorted[1].depth_value).toBe(0.5);
      expect(sorted[2].depth_value).toBe(0.8);
    });

    it('should not modify original array', () => {
      const planes: DepthPlane[] = [
        createDefaultPlane('Far', 0.8),
        createDefaultPlane('Near', 0.2),
      ];

      sortPlanesByDepth(planes);

      expect(planes[0].depth_value).toBe(0.8);
      expect(planes[1].depth_value).toBe(0.2);
    });

    it('should handle empty array', () => {
      expect(sortPlanesByDepth([])).toEqual([]);
    });
  });

  // ============================================
  // getVisiblePlanes Tests
  // ============================================
  describe('getVisiblePlanes', () => {
    it('should return only visible planes', () => {
      const visiblePlane = createDefaultPlane('Visible');
      const hiddenPlane = { ...createDefaultPlane('Hidden'), visible: false };

      const result = getVisiblePlanes([visiblePlane, hiddenPlane]);

      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('Visible');
    });

    it('should return empty array if no visible planes', () => {
      const hiddenPlane = { ...createDefaultPlane('Hidden'), visible: false };

      expect(getVisiblePlanes([hiddenPlane])).toEqual([]);
    });
  });

  // ============================================
  // getVisibleLayers Tests
  // ============================================
  describe('getVisibleLayers', () => {
    it('should return only visible layers', () => {
      const visibleLayer = createDefaultLayer('Visible');
      const hiddenLayer = { ...createDefaultLayer('Hidden'), visible: false };

      const result = getVisibleLayers([visibleLayer, hiddenLayer]);

      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('Visible');
    });
  });

  // ============================================
  // getUnlockedLayers Tests
  // ============================================
  describe('getUnlockedLayers', () => {
    it('should return only unlocked layers', () => {
      const unlockedLayer = createDefaultLayer('Unlocked');
      const lockedLayer = { ...createDefaultLayer('Locked'), locked: true };

      const result = getUnlockedLayers([unlockedLayer, lockedLayer]);

      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('Unlocked');
    });
  });

  // ============================================
  // findPlaneById Tests
  // ============================================
  describe('findPlaneById', () => {
    let planes: DepthPlane[];

    beforeEach(() => {
      planes = [
        createDefaultPlane('Plane 1'),
        createDefaultPlane('Plane 2'),
        createDefaultPlane('Plane 3'),
      ];
    });

    it('should find plane by ID', () => {
      const found = findPlaneById(planes, planes[1].id);

      expect(found?.name).toBe('Plane 2');
    });

    it('should return undefined if not found', () => {
      expect(findPlaneById(planes, 'non-existent')).toBeUndefined();
    });
  });

  // ============================================
  // findLayerById Tests
  // ============================================
  describe('findLayerById', () => {
    let layers: DepthLayer[];

    beforeEach(() => {
      layers = [
        createDefaultLayer('Layer 1'),
        createDefaultLayer('Layer 2'),
        createDefaultLayer('Layer 3'),
      ];
    });

    it('should find layer by ID', () => {
      const found = findLayerById(layers, layers[1].id);

      expect(found?.name).toBe('Layer 2');
    });

    it('should return undefined if not found', () => {
      expect(findLayerById(layers, 'non-existent')).toBeUndefined();
    });
  });

  // ============================================
  // updatePlane Tests
  // ============================================
  describe('updatePlane', () => {
    let planes: DepthPlane[];

    beforeEach(() => {
      planes = [createDefaultPlane('Plane 1'), createDefaultPlane('Plane 2')];
    });

    it('should update plane properties', () => {
      const updated = updatePlane(planes, planes[0].id, { name: 'Updated', depth_value: 0.8 });

      expect(updated[0].name).toBe('Updated');
      expect(updated[0].depth_value).toBe(0.8);
    });

    it('should not modify other planes', () => {
      const originalName = planes[1].name;
      updatePlane(planes, planes[0].id, { name: 'Updated' });

      expect(planes[1].name).toBe(originalName);
    });

    it('should return same array if plane not found', () => {
      const updated = updatePlane(planes, 'non-existent', { name: 'Updated' });

      expect(updated[0].name).toBe('Plane 1');
      expect(updated[1].name).toBe('Plane 2');
    });
  });

  // ============================================
  // updateLayer Tests
  // ============================================
  describe('updateLayer', () => {
    let layers: DepthLayer[];

    beforeEach(() => {
      layers = [createDefaultLayer('Layer 1'), createDefaultLayer('Layer 2')];
    });

    it('should update layer properties', () => {
      const updated = updateLayer(layers, layers[0].id, { opacity: 0.5, visible: false });

      expect(updated[0].opacity).toBe(0.5);
      expect(updated[0].visible).toBe(false);
    });

    it('should update blend mode', () => {
      const updated = updateLayer(layers, layers[0].id, { blend_mode: 'multiply' });

      expect(updated[0].blend_mode).toBe('multiply');
    });
  });

  // ============================================
  // removePlane Tests
  // ============================================
  describe('removePlane', () => {
    let planes: DepthPlane[];

    beforeEach(() => {
      planes = [createDefaultPlane('Plane 1'), createDefaultPlane('Plane 2')];
    });

    it('should remove plane by ID', () => {
      const idToRemove = planes[0].id;
      const remaining = removePlane(planes, idToRemove);

      expect(remaining).toHaveLength(1);
      expect(remaining[0].name).toBe('Plane 2');
    });

    it('should return same array if plane not found', () => {
      const remaining = removePlane(planes, 'non-existent');

      expect(remaining).toHaveLength(2);
    });

    it('should handle empty array', () => {
      expect(removePlane([], 'any')).toEqual([]);
    });
  });

  // ============================================
  // removeLayer Tests
  // ============================================
  describe('removeLayer', () => {
    let layers: DepthLayer[];

    beforeEach(() => {
      layers = [createDefaultLayer('Layer 1'), createDefaultLayer('Layer 2')];
    });

    it('should remove layer by ID', () => {
      const idToRemove = layers[0].id;
      const remaining = removeLayer(layers, idToRemove);

      expect(remaining).toHaveLength(1);
      expect(remaining[0].name).toBe('Layer 2');
    });
  });

  // ============================================
  // createDepthMapExport Tests
  // ============================================
  describe('createDepthMapExport', () => {
    it('should create export from config', () => {
      const config: InteractiveDepthEditorConfig = {
        width: 1920,
        height: 1080,
        layers: [createDefaultLayer('Layer 1')],
        planes: [createDefaultPlane('Plane 1'), createDefaultPlane('Plane 2')],
        active_layer_id: null,
        active_plane_id: null,
      };

      const exportData = createDepthMapExport(config, 'base64data');

      expect(exportData.width).toBe(1920);
      expect(exportData.height).toBe(1080);
      expect(exportData.data).toBe('base64data');
      expect(exportData.planes).toHaveLength(2);
    });

    it('should copy planes from config', () => {
      const config: InteractiveDepthEditorConfig = {
        width: 640,
        height: 480,
        layers: [],
        planes: [createDefaultPlane('Plane 1')],
        active_layer_id: null,
        active_plane_id: null,
      };

      const exportData = createDepthMapExport(config, 'data');

      expect(exportData.planes).toEqual(config.planes);
    });
  });

  // ============================================
  // Integration Tests
  // ============================================
  describe('Integration Tests', () => {
    it('should support full workflow: create, update, filter, export', () => {
      // 1. Create default config
      const config = createDefaultConfig(1920, 1080);
      expect(config.layers).toHaveLength(1);

      // 2. Add a plane
      const plane = createDefaultPlane('Foreground', 0.2);
      const configWithPlane = {
        ...config,
        planes: [...config.planes, plane],
        active_plane_id: plane.id,
      };

      // 3. Update the plane
      configWithPlane.planes = updatePlane(configWithPlane.planes, plane.id, {
        points: [
          { x: 0, y: 0 },
          { x: 0.5, y: 0 },
          { x: 0.5, y: 1 },
          { x: 0, y: 1 },
        ],
      });

      expect(configWithPlane.planes[0].points).toHaveLength(4);

      // 4. Add another layer
      const newLayer = createDefaultLayer('Overlay');
      newLayer.opacity = 0.5;
      newLayer.blend_mode = 'overlay';

      const configWithLayers = {
        ...configWithPlane,
        layers: [...configWithPlane.layers, newLayer],
      };

      // 5. Filter visible layers
      const visibleLayers = getVisibleLayers(configWithLayers.layers);
      expect(visibleLayers).toHaveLength(2);

      // 6. Create export
      const exportData = createDepthMapExport(configWithLayers, 'exportdata');
      expect(exportData.width).toBe(1920);
      expect(exportData.planes).toHaveLength(1);
    });

    it('should handle locking workflow', () => {
      const layer1 = createDefaultLayer('Layer 1');
      const layer2 = createDefaultLayer('Layer 2');
      layer2.locked = true;

      const layers = [layer1, layer2];

      // Get unlocked layers
      const unlocked = getUnlockedLayers(layers);
      expect(unlocked).toHaveLength(1);
      expect(unlocked[0].name).toBe('Layer 1');

      // Try to update locked layer (should still work as it's just data)
      const updated = updateLayer(layers, layer2.id, { opacity: 0.3 });
      expect(updated[1].opacity).toBe(0.3);
    });
  });
});
