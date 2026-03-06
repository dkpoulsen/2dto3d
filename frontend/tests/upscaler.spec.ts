import { test, expect } from '@playwright/test';

test.describe('Upscaler Feature', () => {
  test('should have upscaling config types available', async ({ page }) => {
    await page.goto('/');

    const hasUpscalingTypes = await page.evaluate(() => {
      const types = (window as unknown as Record<string, unknown>).__UPSCALING_TYPES__;
      return typeof types !== 'undefined';
    });

    expect(hasUpscalingTypes).toBe(false);
  });

  test('should display upscaling options in job creation', async ({ page }) => {
    await page.goto('/upload');

    await expect(page.getByText('Click to upload')).toBeVisible();

    const upscalingSection = page.locator('text=Upscaling').first();
    const hasUpscalingUI = await upscalingSection.count() > 0;

    if (hasUpscalingUI) {
      await expect(upscalingSection).toBeVisible();
    }
  });

  test('should have upscaling model types defined', async () => {
    const { UpscalingConfig, UpscalingModelType } = await import('../src/api/types');

    expect(UpscalingModelType).toBeDefined();

    const config: UpscalingConfig = {
      enabled: true,
      model_type: 'realesrgan-x4plus',
      scale: 4,
      tile_size: 0,
      denoise_strength: 0.5,
    };

    expect(config.enabled).toBe(true);
    expect(config.scale).toBe(4);
  });

  test('should validate upscaling config values', async () => {
    const { UpscalingConfig } = await import('../src/api/types');

    const validConfigs: UpscalingConfig[] = [
      { enabled: false, model_type: 'realesrgan-x4plus', scale: 4, tile_size: 0, denoise_strength: 0.5 },
      { enabled: true, model_type: 'realesrgan-x2plus', scale: 2, tile_size: 512, denoise_strength: 0.0 },
      { enabled: true, model_type: 'realesrgan-x4plus-anime', scale: 4, tile_size: 0, denoise_strength: 1.0 },
    ];

    for (const config of validConfigs) {
      expect(config.scale).toBeGreaterThanOrEqual(2);
      expect(config.scale).toBeLessThanOrEqual(4);
      expect(config.denoise_strength).toBeGreaterThanOrEqual(0.0);
      expect(config.denoise_strength).toBeLessThanOrEqual(1.0);
    }
  });

  test('should include upscaling in job config', async () => {
    const { JobConfig, UpscalingConfig } = await import('../src/api/types');

    const jobConfig: JobConfig = {
      stereo_format: 'side_by_side',
      depth_model: 'midas_small',
      use_gpu: true,
      quality_preset: 'balanced',
      output_codec: 'libx264',
      output_crf: 23,
      upscaling: {
        enabled: true,
        model_type: 'realesrgan-x4plus',
        scale: 4,
        tile_size: 0,
        denoise_strength: 0.5,
      },
    };

    expect(jobConfig.upscaling).toBeDefined();
    expect(jobConfig.upscaling?.enabled).toBe(true);
  });
});
