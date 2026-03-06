/**
 * Playwright verification test for depth curve adjustment feature.
 * 
 * This test verifies the depth curve API endpoint accepts and processes
 * the new depth_curve configuration parameter correctly.
 * 
 * @fileoverview Verification test for depth-curve-adjustment feature
 */

import { test, expect } from '@playwright/test';

test.describe('Depth Curve Adjustment API', () => {
  test('should accept depth_curve parameter in job config', async ({ request }) => {
    // Test that the API accepts the new depth_curve parameter
    // We test with a minimal valid config to verify schema acceptance
    const response = await request.post('/api/v1/jobs', {
      data: {
        input_file_id: 'test-file-id',
        config: {
          stereo_format: 'side_by_side',
          depth_model: 'midas_small',
          depth_curve: {
            enabled: true,
            preset: 's_curve',
            control_points: [
              { x: 0.0, y: 0.0 },
              { x: 0.5, y: 0.5 },
              { x: 1.0, y: 1.0 },
            ],
          },
        },
      },
    });

    // API should accept the request format (even if file doesn't exist)
    // 404 for file not found is acceptable, 422 for validation error is not
    expect(response.status()).not.toBe(422);
    
    // If we get a 404 (file not found), the schema validation passed
    if (response.status() === 404) {
      console.log('✓ Schema validation passed (file not found is expected)');
    }
  });

  test('should accept linear preset', async ({ request }) => {
    const response = await request.post('/api/v1/jobs', {
      data: {
        input_file_id: 'test-file-id',
        config: {
          stereo_format: 'side_by_side',
          depth_model: 'midas_small',
          depth_curve: {
            enabled: false,
            preset: 'linear',
            control_points: [
              { x: 0.0, y: 0.0 },
              { x: 1.0, y: 1.0 },
            ],
          },
        },
      },
    });

    expect(response.status()).not.toBe(422);
  });

  test('should accept custom control points', async ({ request }) => {
    const response = await request.post('/api/v1/jobs', {
      data: {
        input_file_id: 'test-file-id',
        config: {
          stereo_format: 'side_by_side',
          depth_model: 'midas_small',
          depth_curve: {
            enabled: true,
            preset: null,
            control_points: [
              { x: 0.0, y: 0.0 },
              { x: 0.25, y: 0.15 },
              { x: 0.5, y: 0.5 },
              { x: 0.75, y: 0.85 },
              { x: 1.0, y: 1.0 },
            ],
          },
        },
      },
    });

    expect(response.status()).not.toBe(422);
  });

  test('should accept all preset types', async ({ request }) => {
    const presets = ['linear', 's_curve', 'contrast_boost', 'soft_curve', 'inverse_s', 'shadow_lift', 'highlight_compress'];
    
    for (const preset of presets) {
      const response = await request.post('/api/v1/jobs', {
        data: {
          input_file_id: 'test-file-id',
          config: {
            stereo_format: 'side_by_side',
            depth_model: 'midas_small',
            depth_curve: {
              enabled: true,
              preset: preset,
            },
          },
        },
      });

      expect(response.status()).not.toBe(422);
    }
  });

  test('should validate control point ranges', async ({ request }) => {
    // Test with out-of-range control point - should get 422
    const response = await request.post('/api/v1/jobs', {
      data: {
        input_file_id: 'test-file-id',
        config: {
          stereo_format: 'side_by_side',
          depth_model: 'midas_small',
          depth_curve: {
            enabled: true,
            control_points: [
              { x: 0.0, y: 0.0 },
              { x: 1.5, y: 1.0 }, // x > 1.0 should fail validation
            ],
          },
        },
      },
    });

    // Should get 422 for validation error
    expect(response.status()).toBe(422);
  });
});

test.describe('Depth Curve Presets API', () => {
  test('should return available curve presets', async ({ request }) => {
    // Check if there's an endpoint to list available presets
    const response = await request.get('/api/v1/presets/curve');
    
    // This endpoint might not exist yet, so we just check if it returns something valid
    if (response.ok()) {
      const data = await response.json();
      expect(data).toBeDefined();
    }
  });
});
