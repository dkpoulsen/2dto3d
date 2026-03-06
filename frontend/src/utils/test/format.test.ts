import { describe, it, expect } from 'vitest';
import {
  formatBytes,
  formatMegabytes,
  formatDate,
  formatDuration,
  formatUptime,
  capitalize,
} from '../format';

describe('formatBytes', () => {
  it('should format 0 bytes', () => {
    expect(formatBytes(0)).toBe('0 B');
  });

  it('should format bytes', () => {
    expect(formatBytes(500)).toBe('500 B');
  });

  it('should format kilobytes', () => {
    expect(formatBytes(1024)).toBe('1 KB');
    expect(formatBytes(1536)).toBe('1.5 KB');
  });

  it('should format megabytes', () => {
    expect(formatBytes(1048576)).toBe('1 MB');
    expect(formatBytes(1572864)).toBe('1.5 MB');
  });

  it('should format gigabytes', () => {
    expect(formatBytes(1073741824)).toBe('1 GB');
  });

  it('should format terabytes', () => {
    expect(formatBytes(1099511627776)).toBe('1 TB');
  });

  it('should handle small values correctly', () => {
    expect(formatBytes(1)).toBe('1 B');
    expect(formatBytes(100)).toBe('100 B');
  });
});

describe('formatMegabytes', () => {
  it('should format megabytes to bytes string', () => {
    expect(formatMegabytes(1)).toBe('1 MB');
  });

  it('should handle 0 megabytes', () => {
    expect(formatMegabytes(0)).toBe('0 B');
  });

  it('should format gigabytes', () => {
    expect(formatMegabytes(1024)).toBe('1 GB');
  });
});

describe('formatDate', () => {
  it('should format valid date string', () => {
    const dateStr = '2024-01-15T10:30:00Z';
    const result = formatDate(dateStr);
    expect(result).toBeTruthy();
    expect(typeof result).toBe('string');
  });

  it('should return dash for null date', () => {
    expect(formatDate(null)).toBe('-');
  });

  it('should handle ISO date strings', () => {
    const result = formatDate('2024-06-20T14:30:00.000Z');
    expect(result).toMatch(/2024/);
  });
});

describe('formatDuration', () => {
  it('should return dash for null', () => {
    expect(formatDuration(null)).toBe('-');
  });

  it('should return dash for 0', () => {
    expect(formatDuration(0)).toBe('-');
  });

  it('should format seconds only', () => {
    expect(formatDuration(45)).toBe('45s');
  });

  it('should format minutes and seconds', () => {
    expect(formatDuration(125)).toBe('2m 5s');
  });

  it('should format hours, minutes, and seconds', () => {
    expect(formatDuration(3725)).toBe('1h 2m 5s');
  });

  it('should format days, hours, minutes, and seconds', () => {
    expect(formatDuration(90125)).toBe('1d 1h 2m 5s');
  });
});

describe('formatUptime', () => {
  it('should format minutes only', () => {
    expect(formatUptime(300)).toBe('5m');
  });

  it('should format hours and minutes', () => {
    expect(formatUptime(3661)).toBe('1h 1m');
  });

  it('should handle 0 seconds', () => {
    expect(formatUptime(0)).toBe('0m');
  });

  it('should handle less than a minute', () => {
    expect(formatUptime(30)).toBe('0m');
  });
});

describe('capitalize', () => {
  it('should capitalize first letter', () => {
    expect(capitalize('hello')).toBe('Hello');
    expect(capitalize('world')).toBe('World');
  });

  it('should handle already capitalized strings', () => {
    expect(capitalize('Hello')).toBe('Hello');
  });

  it('should handle single character', () => {
    expect(capitalize('a')).toBe('A');
  });

  it('should preserve rest of string', () => {
    expect(capitalize('hELLO')).toBe('HELLO');
  });

  it('should handle empty string', () => {
    expect(capitalize('')).toBe('');
  });
});
