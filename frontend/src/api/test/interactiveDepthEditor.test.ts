import { describe, it, expect } from 'vitest';
import type {
  DepthPlane,
  DepthLayer,
  InteractiveDepthEditorConfig,
  DepthMapExport,
} from '../types';

// ============================================
// Type Safety Tests for Interactive Depth Editor
// ============================================
describe('Interactive Depth Editor Types', () => {
  // ============================================
  // DepthPlane Type Tests
  // ============================================
  describe('DepthPlane', () => {
    it('should accept a valid DepthPlane with all required fields', () => {
      const plane: DepthPlane = {
        id: 'plane-1',
        name: 'Foreground',
        depth_value: 0.1,
        color: '#ff0000',
        visible: true,
        locked: false,
        points: [
          { x: 0.1, y: 0.1 },
          { x: 0.5, y: 0.1 },
          { x: 0.5, y: 0.5 },
          { x: 0.1, y: 0.5 },
        ],
      };

      expect(plane.id).toBe('plane-1');
      expect(plane.name).toBe('Foreground');
      expect(plane.depth_value).toBe(0.1);
      expect(plane.visible).toBe(true);
      expect(plane.points).toHaveLength(4);
    });

    it('should accept depth_value at boundaries (0 and 1)', () => {
      const nearPlane: DepthPlane = {
        id: 'near',
        name: 'Near',
        depth_value: 0,
        color: '#000000',
        visible: true,
        locked: false,
        points: [],
      };

      const farPlane: DepthPlane = {
        id: 'far',
        name: 'Far',
        depth_value: 1,
        color: '#ffffff',
        visible: true,
        locked: false,
        points: [],
      };

      expect(nearPlane.depth_value).toBe(0);
      expect(farPlane.depth_value).toBe(1);
    });

    it('should support different visibility and lock states', () => {
      const hiddenLockedPlane: DepthPlane = {
        id: 'hidden-locked',
        name: 'Hidden Layer',
        depth_value: 0.5,
        color: '#808080',
        visible: false,
        locked: true,
        points: [{ x: 0.5, y: 0.5 }],
      };

      expect(hiddenLockedPlane.visible).toBe(false);
      expect(hiddenLockedPlane.locked).toBe(true);
    });

    it('should accept empty points array for full-frame plane', () => {
      const fullFramePlane: DepthPlane = {
        id: 'full-frame',
        name: 'Full Frame',
        depth_value: 0.5,
        color: '#404040',
        visible: true,
        locked: false,
        points: [],
      };

      expect(fullFramePlane.points).toEqual([]);
    });

    it('should support complex polygon points', () => {
      const complexPlane: DepthPlane = {
        id: 'complex',
        name: 'Complex Shape',
        depth_value: 0.7,
        color: '#00ff00',
        visible: true,
        locked: false,
        points: [
          { x: 0.25, y: 0.25 },
          { x: 0.75, y: 0.25 },
          { x: 0.75, y: 0.75 },
          { x: 0.5, y: 0.9 },
          { x: 0.25, y: 0.75 },
        ],
      };

      expect(complexPlane.points).toHaveLength(5);
      expect(complexPlane.points[3].x).toBe(0.5);
      expect(complexPlane.points[3].y).toBe(0.9);
    });
  });

  // ============================================
  // DepthLayer Type Tests
  // ============================================
  describe('DepthLayer', () => {
    it('should accept a valid DepthLayer with all required fields', () => {
      const layer: DepthLayer = {
        id: 'layer-1',
        name: 'Base Layer',
        visible: true,
        locked: false,
        opacity: 1,
        blend_mode: 'normal',
        data: null,
      };

      expect(layer.id).toBe('layer-1');
      expect(layer.name).toBe('Base Layer');
      expect(layer.opacity).toBe(1);
      expect(layer.blend_mode).toBe('normal');
      expect(layer.data).toBeNull();
    });

    it('should accept all blend modes', () => {
      const blendModes: DepthLayer['blend_mode'][] = [
        'normal',
        'multiply',
        'screen',
        'overlay',
      ];

      blendModes.forEach((mode, index) => {
        const layer: DepthLayer = {
          id: `layer-${index}`,
          name: `Layer ${index}`,
          visible: true,
          locked: false,
          opacity: 1,
          blend_mode: mode,
          data: null,
        };

        expect(layer.blend_mode).toBe(mode);
      });
    });

    it('should accept opacity at boundaries (0 and 1)', () => {
      const invisibleLayer: DepthLayer = {
        id: 'invisible',
        name: 'Invisible',
        visible: true,
        locked: false,
        opacity: 0,
        blend_mode: 'normal',
        data: null,
      };

      const opaqueLayer: DepthLayer = {
        id: 'opaque',
        name: 'Opaque',
        visible: true,
        locked: false,
        opacity: 1,
        blend_mode: 'normal',
        data: null,
      };

      expect(invisibleLayer.opacity).toBe(0);
      expect(opaqueLayer.opacity).toBe(1);
    });

    it('should accept fractional opacity values', () => {
      const semiTransparentLayer: DepthLayer = {
        id: 'semi',
        name: 'Semi-Transparent',
        visible: true,
        locked: false,
        opacity: 0.5,
        blend_mode: 'overlay',
        data: null,
      };

      expect(semiTransparentLayer.opacity).toBe(0.5);
    });

    it('should accept Base64 encoded PNG data', () => {
      const layerWithData: DepthLayer = {
        id: 'with-data',
        name: 'Layer with Data',
        visible: true,
        locked: false,
        opacity: 1,
        blend_mode: 'normal',
        data: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
      };

      expect(layerWithData.data).toContain('base64');
      expect(layerWithData.data).toContain('image/png');
    });

    it('should support locked invisible layer', () => {
      const lockedHiddenLayer: DepthLayer = {
        id: 'locked-hidden',
        name: 'Locked Hidden Layer',
        visible: false,
        locked: true,
        opacity: 0.3,
        blend_mode: 'multiply',
        data: null,
      };

      expect(lockedHiddenLayer.visible).toBe(false);
      expect(lockedHiddenLayer.locked).toBe(true);
    });
  });

  // ============================================
  // InteractiveDepthEditorConfig Type Tests
  // ============================================
  describe('InteractiveDepthEditorConfig', () => {
    it('should accept a valid config with all fields', () => {
      const config: InteractiveDepthEditorConfig = {
        width: 1920,
        height: 1080,
        layers: [],
        planes: [],
        active_layer_id: null,
        active_plane_id: null,
      };

      expect(config.width).toBe(1920);
      expect(config.height).toBe(1080);
      expect(config.layers).toEqual([]);
      expect(config.planes).toEqual([]);
      expect(config.active_layer_id).toBeNull();
      expect(config.active_plane_id).toBeNull();
    });

    it('should accept config with layers and planes', () => {
      const layer: DepthLayer = {
        id: 'layer-1',
        name: 'Layer 1',
        visible: true,
        locked: false,
        opacity: 1,
        blend_mode: 'normal',
        data: null,
      };

      const plane: DepthPlane = {
        id: 'plane-1',
        name: 'Plane 1',
        depth_value: 0.5,
        color: '#ff0000',
        visible: true,
        locked: false,
        points: [{ x: 0.5, y: 0.5 }],
      };

      const config: InteractiveDepthEditorConfig = {
        width: 640,
        height: 480,
        layers: [layer],
        planes: [plane],
        active_layer_id: 'layer-1',
        active_plane_id: 'plane-1',
      };

      expect(config.layers).toHaveLength(1);
      expect(config.planes).toHaveLength(1);
      expect(config.active_layer_id).toBe('layer-1');
      expect(config.active_plane_id).toBe('plane-1');
    });

    it('should support multiple layers with different blend modes', () => {
      const layers: DepthLayer[] = [
        {
          id: 'base',
          name: 'Base',
          visible: true,
          locked: false,
          opacity: 1,
          blend_mode: 'normal',
          data: null,
        },
        {
          id: 'multiply',
          name: 'Multiply',
          visible: true,
          locked: false,
          opacity: 0.8,
          blend_mode: 'multiply',
          data: null,
        },
        {
          id: 'screen',
          name: 'Screen',
          visible: true,
          locked: false,
          opacity: 0.6,
          blend_mode: 'screen',
          data: null,
        },
      ];

      const config: InteractiveDepthEditorConfig = {
        width: 1280,
        height: 720,
        layers,
        planes: [],
        active_layer_id: 'base',
        active_plane_id: null,
      };

      expect(config.layers).toHaveLength(3);
      expect(config.layers[0].blend_mode).toBe('normal');
      expect(config.layers[1].blend_mode).toBe('multiply');
      expect(config.layers[2].blend_mode).toBe('screen');
    });

    it('should support multiple depth planes at different depths', () => {
      const planes: DepthPlane[] = [
        {
          id: 'foreground',
          name: 'Foreground',
          depth_value: 0.1,
          color: '#ff0000',
          visible: true,
          locked: false,
          points: [],
        },
        {
          id: 'midground',
          name: 'Midground',
          depth_value: 0.5,
          color: '#00ff00',
          visible: true,
          locked: false,
          points: [],
        },
        {
          id: 'background',
          name: 'Background',
          depth_value: 0.9,
          color: '#0000ff',
          visible: true,
          locked: false,
          points: [],
        },
      ];

      const config: InteractiveDepthEditorConfig = {
        width: 1920,
        height: 1080,
        layers: [],
        planes,
        active_layer_id: null,
        active_plane_id: 'midground',
      };

      expect(config.planes).toHaveLength(3);
      expect(config.planes[0].depth_value).toBe(0.1);
      expect(config.planes[1].depth_value).toBe(0.5);
      expect(config.planes[2].depth_value).toBe(0.9);
    });
  });

  // ============================================
  // DepthMapExport Type Tests
  // ============================================
  describe('DepthMapExport', () => {
    it('should accept a valid DepthMapExport with all fields', () => {
      const exportData: DepthMapExport = {
        width: 640,
        height: 480,
        data: 'data:image/png;base64,test',
        planes: [],
      };

      expect(exportData.width).toBe(640);
      expect(exportData.height).toBe(480);
      expect(exportData.data).toContain('base64');
      expect(exportData.planes).toEqual([]);
    });

    it('should accept export with depth planes', () => {
      const planes: DepthPlane[] = [
        {
          id: 'plane-1',
          name: 'Plane 1',
          depth_value: 0.3,
          color: '#ff0000',
          visible: true,
          locked: false,
          points: [{ x: 0.1, y: 0.1 }],
        },
        {
          id: 'plane-2',
          name: 'Plane 2',
          depth_value: 0.7,
          color: '#0000ff',
          visible: true,
          locked: false,
          points: [{ x: 0.9, y: 0.9 }],
        },
      ];

      const exportData: DepthMapExport = {
        width: 1920,
        height: 1080,
        data: 'data:image/png;base64,compresseddepthmap',
        planes,
      };

      expect(exportData.planes).toHaveLength(2);
      expect(exportData.planes[0].depth_value).toBe(0.3);
      expect(exportData.planes[1].depth_value).toBe(0.7);
    });

    it('should support various image dimensions', () => {
      const resolutions = [
        { width: 640, height: 480 },
        { width: 1280, height: 720 },
        { width: 1920, height: 1080 },
        { width: 3840, height: 2160 },
        { width: 800, height: 600 },
      ];

      resolutions.forEach(({ width, height }) => {
        const exportData: DepthMapExport = {
          width,
          height,
          data: 'data:image/png;base64,test',
          planes: [],
        };

        expect(exportData.width).toBe(width);
        expect(exportData.height).toBe(height);
      });
    });
  });

  // ============================================
  // Integration Tests
  // ============================================
  describe('Integration Tests', () => {
    it('should support creating a complete editor configuration', () => {
      // Create layers
      const baseLayer: DepthLayer = {
        id: 'base',
        name: 'Base Depth',
        visible: true,
        locked: false,
        opacity: 1,
        blend_mode: 'normal',
        data: null,
      };

      const overlayLayer: DepthLayer = {
        id: 'overlay',
        name: 'Detail Overlay',
        visible: true,
        locked: false,
        opacity: 0.5,
        blend_mode: 'overlay',
        data: 'data:image/png;base64,overlaydata',
      };

      // Create planes
      const foregroundPlane: DepthPlane = {
        id: 'fg',
        name: 'Foreground',
        depth_value: 0.2,
        color: '#ff0000',
        visible: true,
        locked: false,
        points: [
          { x: 0, y: 0 },
          { x: 0.4, y: 0 },
          { x: 0.4, y: 1 },
          { x: 0, y: 1 },
        ],
      };

      const backgroundPlane: DepthPlane = {
        id: 'bg',
        name: 'Background',
        depth_value: 0.8,
        color: '#0000ff',
        visible: true,
        locked: false,
        points: [
          { x: 0.6, y: 0 },
          { x: 1, y: 0 },
          { x: 1, y: 1 },
          { x: 0.6, y: 1 },
        ],
      };

      // Create config
      const config: InteractiveDepthEditorConfig = {
        width: 1920,
        height: 1080,
        layers: [baseLayer, overlayLayer],
        planes: [foregroundPlane, backgroundPlane],
        active_layer_id: 'overlay',
        active_plane_id: 'fg',
      };

      // Create export
      const exportData: DepthMapExport = {
        width: config.width,
        height: config.height,
        data: 'data:image/png;base64,finaldepthmap',
        planes: config.planes,
      };

      // Verify complete workflow
      expect(config.layers).toHaveLength(2);
      expect(config.planes).toHaveLength(2);
      expect(exportData.width).toBe(config.width);
      expect(exportData.height).toBe(config.height);
      expect(exportData.planes).toEqual(config.planes);
    });

    it('should support typical layer manipulation workflow', () => {
      // Initial state
      const initialConfig: InteractiveDepthEditorConfig = {
        width: 640,
        height: 480,
        layers: [],
        planes: [],
        active_layer_id: null,
        active_plane_id: null,
      };

      // Add a layer
      const newLayer: DepthLayer = {
        id: 'layer-1',
        name: 'New Layer',
        visible: true,
        locked: false,
        opacity: 1,
        blend_mode: 'normal',
        data: null,
      };

      const configWithLayer: InteractiveDepthEditorConfig = {
        ...initialConfig,
        layers: [...initialConfig.layers, newLayer],
        active_layer_id: newLayer.id,
      };

      expect(configWithLayer.layers).toHaveLength(1);
      expect(configWithLayer.active_layer_id).toBe('layer-1');

      // Modify layer
      const modifiedLayers = configWithLayer.layers.map((layer) =>
        layer.id === 'layer-1' ? { ...layer, opacity: 0.7 } : layer
      );

      expect(modifiedLayers[0].opacity).toBe(0.7);

      // Delete layer
      const configAfterDelete: InteractiveDepthEditorConfig = {
        ...configWithLayer,
        layers: configWithLayer.layers.filter((l) => l.id !== 'layer-1'),
        active_layer_id: null,
      };

      expect(configAfterDelete.layers).toHaveLength(0);
      expect(configAfterDelete.active_layer_id).toBeNull();
    });

    it('should support typical plane manipulation workflow', () => {
      // Create initial plane
      const plane: DepthPlane = {
        id: 'plane-1',
        name: 'First Plane',
        depth_value: 0.5,
        color: '#808080',
        visible: true,
        locked: false,
        points: [],
      };

      // Add points to plane
      const planeWithPoints: DepthPlane = {
        ...plane,
        points: [
          { x: 0.2, y: 0.2 },
          { x: 0.8, y: 0.2 },
          { x: 0.8, y: 0.8 },
          { x: 0.2, y: 0.8 },
        ],
      };

      expect(planeWithPoints.points).toHaveLength(4);

      // Toggle visibility
      const hiddenPlane: DepthPlane = {
        ...planeWithPoints,
        visible: false,
      };

      expect(hiddenPlane.visible).toBe(false);

      // Lock plane
      const lockedPlane: DepthPlane = {
        ...planeWithPoints,
        locked: true,
      };

      expect(lockedPlane.locked).toBe(true);
    });
  });

  // ============================================
  // Edge Cases
  // ============================================
  describe('Edge Cases', () => {
    it('should handle layers with same blend mode', () => {
      const layers: DepthLayer[] = [
        {
          id: 'layer-1',
          name: 'Layer 1',
          visible: true,
          locked: false,
          opacity: 0.3,
          blend_mode: 'multiply',
          data: null,
        },
        {
          id: 'layer-2',
          name: 'Layer 2',
          visible: true,
          locked: false,
          opacity: 0.5,
          blend_mode: 'multiply',
          data: null,
        },
      ];

      expect(layers.every((l) => l.blend_mode === 'multiply')).toBe(true);
    });

    it('should handle planes with same depth value', () => {
      const planes: DepthPlane[] = [
        {
          id: 'plane-1',
          name: 'Left',
          depth_value: 0.5,
          color: '#ff0000',
          visible: true,
          locked: false,
          points: [{ x: 0, y: 0 }],
        },
        {
          id: 'plane-2',
          name: 'Right',
          depth_value: 0.5,
          color: '#00ff00',
          visible: true,
          locked: false,
          points: [{ x: 1, y: 1 }],
        },
      ];

      expect(planes[0].depth_value).toBe(planes[1].depth_value);
    });

    it('should handle zero-dimension configs', () => {
      const config: InteractiveDepthEditorConfig = {
        width: 0,
        height: 0,
        layers: [],
        planes: [],
        active_layer_id: null,
        active_plane_id: null,
      };

      expect(config.width).toBe(0);
      expect(config.height).toBe(0);
    });

    it('should handle very large dimensions', () => {
      const config: InteractiveDepthEditorConfig = {
        width: 10000,
        height: 10000,
        layers: [],
        planes: [],
        active_layer_id: null,
        active_plane_id: null,
      };

      expect(config.width).toBe(10000);
      expect(config.height).toBe(10000);
    });
  });
});
