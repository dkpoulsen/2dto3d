import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Undo2,
  Redo2,
  RotateCcw,
  Paintbrush,
  Eraser,
  ZoomIn,
  ZoomOut,
  Download,
  Save,
  Eye,
  EyeOff,
} from 'lucide-react';

// Colormap definitions matching backend ColorMapType
type ColormapType = 'turbo' | 'plasma' | 'viridis' | 'magma' | 'jet' | 'inferno' | 'gray';

// Color stops for colormap generation
const COLORMAP_STOPS: Record<ColormapType, [number, number, number][]> = {
  turbo: [
    [48, 18, 59], [66, 58, 131], [68, 99, 160], [60, 137, 170],
    [77, 179, 148], [126, 206, 118], [185, 218, 85], [249, 215, 57],
    [254, 240, 82], [247, 253, 191]
  ],
  plasma: [
    [13, 8, 135], [75, 3, 161], [125, 3, 168], [168, 34, 150],
    [203, 70, 121], [229, 107, 93], [248, 148, 65], [253, 195, 40],
    [240, 249, 33]
  ],
  viridis: [
    [68, 1, 84], [72, 40, 120], [62, 73, 137], [49, 104, 142],
    [38, 130, 142], [31, 158, 137], [53, 183, 121], [109, 205, 89],
    [180, 222, 44], [253, 231, 37]
  ],
  magma: [
    [0, 0, 4], [28, 16, 68], [79, 18, 123], [129, 37, 129],
    [168, 63, 125], [204, 95, 115], [232, 133, 113], [251, 179, 135],
    [252, 226, 187], [252, 253, 191]
  ],
  jet: [
    [0, 0, 127], [0, 0, 255], [0, 127, 255], [0, 255, 255],
    [127, 255, 127], [255, 255, 0], [255, 127, 0], [255, 0, 0], [127, 0, 0]
  ],
  inferno: [
    [0, 0, 4], [22, 11, 57], [66, 10, 104], [106, 23, 110],
    [147, 38, 103], [188, 55, 84], [221, 81, 58], [243, 118, 27],
    [252, 165, 10], [246, 215, 70], [252, 255, 164]
  ],
  gray: [[0, 0, 0], [255, 255, 255]],
};

interface BrushSettings {
  size: number;
  hardness: number;
  value: number; // 0-1 for depth value
}

interface HistoryState {
  imageData: ImageData;
  timestamp: number;
}

interface DepthValidationEditorProps {
  /** Initial depth map as base64 encoded image or ImageData */
  initialDepthMap?: string | ImageData;
  /** Width of the canvas */
  width?: number;
  /** Height of the canvas */
  height?: number;
  /** Callback when depth map is modified */
  onChange?: (depthMap: ImageData) => void;
  /** Callback when save is clicked */
  onSave?: (depthMap: ImageData) => void;
  /** Whether the editor is disabled */
  disabled?: boolean;
  /** Additional CSS class names */
  className?: string;
}
// Constants for brush/editor defaults
const BRUSH_SIZE_STEP = 5;
const ZOOM_STEP = 0.25;
const MIN_ZOOM = 0.25;
const MAX_ZOOM = 4;
const MIN_BRUSH_SIZE = 1;
const MAX_BRUSH_SIZE = 200;
const DEFAULT_BRUSH_SIZE = 20;
const DEFAULT_BRUSH_HARDNESS = 0.8;
const DEFAULT_BRUSH_VALUE = 0.5;
const NEUTRAL_GRAY_VALUE = 0.5;
const MAX_HISTORY = 50;

// Interpolate color from colormap stops
function getColormapColor(value: number, colormap: ColormapType): [number, number, number] {
  const stops = COLORMAP_STOPS[colormap];
  const numStops = stops.length;
  
  // Clamp value to [0, 1]
  const v = Math.max(0, Math.min(1, value));
  
  // Find the two stops to interpolate between
  const scaledV = v * (numStops - 1);
  const lowerIdx = Math.floor(scaledV);
  const upperIdx = Math.min(lowerIdx + 1, numStops - 1);
  const t = scaledV - lowerIdx;
  
  // Linear interpolation
  const lower = stops[lowerIdx];
  const upper = stops[upperIdx];
  
  return [
    Math.round(lower[0] + (upper[0] - lower[0]) * t),
    Math.round(lower[1] + (upper[1] - lower[1]) * t),
    Math.round(lower[2] + (upper[2] - lower[2]) * t),
  ];
}


export function DepthValidationEditor({
  initialDepthMap,
  width = 640,
  height = 480,
  onChange,
  onSave,
  disabled = false,
  className = '',
}: DepthValidationEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Editor state
  const [brushSettings, setBrushSettings] = useState<BrushSettings>({
    size: DEFAULT_BRUSH_SIZE,
    hardness: DEFAULT_BRUSH_HARDNESS,
    value: DEFAULT_BRUSH_VALUE,
  });
  const [colormap, setColormap] = useState<ColormapType>('turbo');
  const [showColormap, setShowColormap] = useState(true);
  const [tool, setTool] = useState<'brush' | 'eraser'>('brush');
  const [zoom, setZoom] = useState(1);
  
  // History for undo/redo
  const [history, setHistory] = useState<HistoryState[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  
  // Drawing state
  // Drawing state
  const [isDrawing, setIsDrawing] = useState(false);
  const [lastPos, setLastPos] = useState<{ x: number; y: number } | null>(null);
  const [cursorPos, setCursorPos] = useState<{ x: number; y: number } | null>(null);
  
  // Initialize canvas with depth map
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;
    
    canvas.width = width;
    canvas.height = height;
    
    if (initialDepthMap) {
      if (typeof initialDepthMap === 'string') {
        // Load from base64
        const img = new Image();
        img.onload = () => {
          ctx.drawImage(img, 0, 0, width, height);
          saveToHistory();
        };
        img.src = initialDepthMap;
      } else {
        // Load from ImageData
        ctx.putImageData(initialDepthMap, 0, 0);
        saveToHistory();
      }
    } else {
      // Fill with neutral gray
      ctx.fillStyle = '#808080';
      ctx.fillRect(0, 0, width, height);
      saveToHistory();
    }
  }, [initialDepthMap, width, height]);
  
  // Initialize overlay canvas
  useEffect(() => {
    const overlay = overlayCanvasRef.current;
    if (!overlay) return;
    
    overlay.width = width;
    overlay.height = height;
  }, [width, height]);
  
  // Save current state to history
  const saveToHistory = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const newState: HistoryState = {
      imageData,
      timestamp: Date.now(),
    };
    
    setHistory(prev => {
      // Remove any future states if we're not at the end
      const newHistory = prev.slice(0, historyIndex + 1);
      // Add new state
      newHistory.push(newState);
      // Limit history size
      if (newHistory.length > MAX_HISTORY) {
        newHistory.shift();
      }
      return newHistory;
    });
    setHistoryIndex(prev => Math.min(prev + 1, MAX_HISTORY - 1));
  }, [historyIndex]);
  
  // Restore state from history
  const restoreFromHistory = useCallback((index: number) => {
    const canvas = canvasRef.current;
    if (!canvas || index < 0 || index >= history.length) return;
    
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;
    
    ctx.putImageData(history[index].imageData, 0, 0);
    setHistoryIndex(index);
    
    if (onChange) {
      onChange(history[index].imageData);
    }
  }, [history, onChange]);
  
  // Undo
  const handleUndo = useCallback(() => {
    if (historyIndex > 0) {
      restoreFromHistory(historyIndex - 1);
    }
  }, [historyIndex, restoreFromHistory]);
  
  // Redo
  const handleRedo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      restoreFromHistory(historyIndex + 1);
    }
  }, [historyIndex, history.length, restoreFromHistory]);
  
  // Reset to initial state
  const handleReset = useCallback(() => {
    if (history.length > 0) {
      restoreFromHistory(0);
    }
  }, [history.length, restoreFromHistory]);
  
  // Get canvas coordinates from mouse event
  const getCanvasCoords = useCallback((e: React.MouseEvent | MouseEvent): { x: number; y: number } | null => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  }, []);
  
  // Draw brush stroke
  const drawBrushStroke = useCallback((
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    lastX?: number,
    lastY?: number
  ) => {
    const { size, hardness, value } = brushSettings;
    const brushValue = tool === 'eraser' ? NEUTRAL_GRAY_VALUE : value;
    const grayValue = Math.round(brushValue * 255);
    const radius = size / 2;
    
    // Helper function to draw a single brush point
    const drawPoint = (px: number, py: number) => {
      ctx.beginPath();
      ctx.arc(px, py, radius, 0, Math.PI * 2);
      
      if (hardness >= 1) {
        // Hard brush - solid color
        ctx.fillStyle = `rgb(${grayValue}, ${grayValue}, ${grayValue})`;
        ctx.fill();
      } else {
        // Soft brush with gradient
        const gradient = ctx.createRadialGradient(px, py, 0, px, py, radius);
        gradient.addColorStop(0, `rgba(${grayValue}, ${grayValue}, ${grayValue}, 1)`);
        gradient.addColorStop(hardness, `rgba(${grayValue}, ${grayValue}, ${grayValue}, 1)`);
        gradient.addColorStop(1, `rgba(${grayValue}, ${grayValue}, ${grayValue}, 0)`);
        ctx.fillStyle = gradient;
        ctx.fill();
      }
    };
    
    // Draw initial point
    drawPoint(x, y);
    
    // Interpolate between last position and current for smooth strokes
    if (lastX !== undefined && lastY !== undefined) {
      const dist = Math.sqrt((x - lastX) ** 2 + (y - lastY) ** 2);
      const step = size / 4;
      const numSteps = Math.ceil(dist / step);
      
      for (let i = 1; i < numSteps; i++) {
        const t = i / numSteps;
        drawPoint(lastX + (x - lastX) * t, lastY + (y - lastY) * t);
      }
    }
  }, [brushSettings, tool]);
  
  // Draw brush cursor overlay
  const drawCursorOverlay = useCallback((x: number, y: number) => {
    const overlay = overlayCanvasRef.current;
    if (!overlay) return;
    
    const ctx = overlay.getContext('2d');
    if (!ctx) return;
    
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    
    // Draw brush circle
    ctx.strokeStyle = tool === 'eraser' ? '#ff6b6b' : '#3b82f6';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.arc(x, y, brushSettings.size / 2, 0, Math.PI * 2);
    ctx.stroke();
    
    // Draw value indicator in center
    ctx.fillStyle = tool === 'eraser' ? '#ff6b6b' : '#3b82f6';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(Math.round(brushSettings.value * 100) + '%', x, y + 4);
  }, [brushSettings.size, brushSettings.value, tool]);
  
  // Clear cursor overlay
  const clearCursorOverlay = useCallback(() => {
    const overlay = overlayCanvasRef.current;
    if (!overlay) return;
    
    const ctx = overlay.getContext('2d');
    if (!ctx) return;
    
    ctx.clearRect(0, 0, overlay.width, overlay.height);
  }, []);
  
  // Mouse event handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (disabled) return;
    
    const coords = getCanvasCoords(e);
    if (!coords) return;
    
    setIsDrawing(true);
    setLastPos(coords);
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;
    
    // Draw single point
    drawBrushStroke(ctx, coords.x, coords.y);
  }, [disabled, getCanvasCoords, drawBrushStroke]);
  
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const coords = getCanvasCoords(e);
    if (!coords) return;
    
    setCursorPos(coords);
    
    if (isDrawing && !disabled) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      if (!ctx) return;
      
      // Draw stroke from last position
      if (lastPos) {
        drawBrushStroke(ctx, coords.x, coords.y, lastPos.x, lastPos.y);
      }
      
      setLastPos(coords);
    }
    
    // Update cursor overlay
    drawCursorOverlay(coords.x, coords.y);
  }, [disabled, getCanvasCoords, isDrawing, lastPos, drawBrushStroke, drawCursorOverlay]);
  
  const handleMouseUp = useCallback(() => {
    if (isDrawing) {
      setIsDrawing(false);
      setLastPos(null);
      saveToHistory();
      
      // Notify parent of change
      const canvas = canvasRef.current;
      if (canvas && onChange) {
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        if (ctx) {
          onChange(ctx.getImageData(0, 0, canvas.width, canvas.height));
        }
      }
    }
  }, [isDrawing, saveToHistory, onChange]);
  
  const handleMouseLeave = useCallback(() => {
    setCursorPos(null);
    clearCursorOverlay();
    if (isDrawing) {
      handleMouseUp();
    }
  }, [isDrawing, handleMouseUp, clearCursorOverlay]);
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (disabled) return;
      
      // Ctrl/Cmd + Z = Undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      }
      // Ctrl/Cmd + Shift + Z or Ctrl/Cmd + Y = Redo
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        handleRedo();
      }
      // [ = Decrease brush size
      if (e.key === '[') {
        setBrushSettings(prev => ({ ...prev, size: Math.max(MIN_BRUSH_SIZE, prev.size - BRUSH_SIZE_STEP) }));
      }
      // ] = Increase brush size
      if (e.key === ']') {
        setBrushSettings(prev => ({ ...prev, size: Math.min(MAX_BRUSH_SIZE, prev.size + BRUSH_SIZE_STEP) }));
      }
      // B = Brush tool
      if (e.key === 'b') {
        setTool('brush');
      }
      // E = Eraser tool
      if (e.key === 'e') {
        setTool('eraser');
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [disabled, handleUndo, handleRedo]);
  
  // Export depth map
  const handleExport = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    // Create a temporary canvas for export
    const exportCanvas = document.createElement('canvas');
    exportCanvas.width = canvas.width;
    exportCanvas.height = canvas.height;
    const exportCtx = exportCanvas.getContext('2d');
    if (!exportCtx) return;
    
    // Copy current depth map
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    
    if (showColormap) {
      // Apply colormap for export
      const data = imageData.data;
      for (let i = 0; i < data.length; i += 4) {
        const depth = data[i] / 255;
        const [r, g, b] = getColormapColor(depth, colormap);
        data[i] = r;
        data[i + 1] = g;
        data[i + 2] = b;
      }
    }
    
    exportCtx.putImageData(imageData, 0, 0);
    
    // Download
    const link = document.createElement('a');
    link.download = 'depth_map.png';
    link.href = exportCanvas.toDataURL('image/png');
    link.click();
  }, [showColormap, colormap]);
  
  // Handle save
  const handleSave = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !onSave) return;
    
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;
    
    onSave(ctx.getImageData(0, 0, canvas.width, canvas.height));
  }, [onSave]);
  
  // Update canvas display when colormap settings change
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;
    
    // We keep the internal data as grayscale
    // The display is handled by the canvas rendering
  }, [colormap, showColormap]);
  
  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < history.length - 1;
  
  return (
    <div className={`depth-validation-editor ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-3 p-2 bg-gray-100 rounded-lg">
        {/* Tool Selection */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setTool('brush')}
            disabled={disabled}
            className={`p-2 rounded-lg transition-colors ${
              tool === 'brush'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-200'
            } ${disabled ? 'opacity-50' : ''}`}
            title="Brush (B)"
          >
            <Paintbrush className="h-4 w-4" />
          </button>
          <button
            onClick={() => setTool('eraser')}
            disabled={disabled}
            className={`p-2 rounded-lg transition-colors ${
              tool === 'eraser'
                ? 'bg-red-100 text-red-700'
                : 'text-gray-600 hover:bg-gray-200'
            } ${disabled ? 'opacity-50' : ''}`}
            title="Eraser (E)"
          >
            <Eraser className="h-4 w-4" />
          </button>
          
          <div className="w-px h-6 bg-gray-300 mx-2" />
          
          {/* History Controls */}
          <button
            onClick={handleUndo}
            disabled={disabled || !canUndo}
            className="p-2 text-gray-600 hover:bg-gray-200 rounded-lg disabled:opacity-50"
            title="Undo (Ctrl+Z)"
          >
            <Undo2 className="h-4 w-4" />
          </button>
          <button
            onClick={handleRedo}
            disabled={disabled || !canRedo}
            className="p-2 text-gray-600 hover:bg-gray-200 rounded-lg disabled:opacity-50"
            title="Redo (Ctrl+Y)"
          >
            <Redo2 className="h-4 w-4" />
          </button>
          <button
            onClick={handleReset}
            disabled={disabled || history.length <= 1}
            className="p-2 text-gray-600 hover:bg-gray-200 rounded-lg disabled:opacity-50"
            title="Reset"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
        
        {/* Brush Settings */}
        <div className="flex items-center gap-4">
          {/* Brush Size */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">Size:</label>
            <input
              type="range"
              min="1"
              max="200"
              value={brushSettings.size}
              onChange={(e) => setBrushSettings(prev => ({ ...prev, size: parseInt(e.target.value) }))}
              disabled={disabled}
              className="w-20 h-2"
            />
            <span className="text-xs text-gray-600 w-8">{brushSettings.size}px</span>
          </div>
          
          {/* Brush Hardness */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">Hardness:</label>
            <input
              type="range"
              min="0"
              max="100"
              value={Math.round(brushSettings.hardness * 100)}
              onChange={(e) => setBrushSettings(prev => ({ ...prev, hardness: parseInt(e.target.value) / 100 }))}
              disabled={disabled}
              className="w-20 h-2"
            />
            <span className="text-xs text-gray-600 w-8">{Math.round(brushSettings.hardness * 100)}%</span>
          </div>
          
          {/* Depth Value */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">Value:</label>
            <input
              type="range"
              min="0"
              max="100"
              value={Math.round(brushSettings.value * 100)}
              onChange={(e) => setBrushSettings(prev => ({ ...prev, value: parseInt(e.target.value) / 100 }))}
              disabled={disabled}
              className="w-20 h-2"
            />
            <div 
              className="w-6 h-6 rounded border border-gray-300"
              style={{
                backgroundColor: `rgb(${Math.round(brushSettings.value * 255)}, ${Math.round(brushSettings.value * 255)}, ${Math.round(brushSettings.value * 255)})`
              }}
            />
          </div>
        </div>
        
        {/* View Controls */}
        <div className="flex items-center gap-1">
          {/* Colormap Toggle */}
          <button
            onClick={() => setShowColormap(!showColormap)}
            disabled={disabled}
            className={`p-2 rounded-lg transition-colors ${
              showColormap
                ? 'bg-purple-100 text-purple-700'
                : 'text-gray-600 hover:bg-gray-200'
            } ${disabled ? 'opacity-50' : ''}`}
            title="Toggle Colormap"
          >
            {showColormap ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
          </button>
          
          {/* Colormap Selector */}
          <select
            value={colormap}
            onChange={(e) => setColormap(e.target.value as ColormapType)}
            disabled={disabled}
            className="text-xs px-2 py-1 border border-gray-300 rounded-lg disabled:opacity-50"
          >
            <option value="turbo">Turbo</option>
            <option value="plasma">Plasma</option>
            <option value="viridis">Viridis</option>
            <option value="magma">Magma</option>
            <option value="jet">Jet</option>
            <option value="inferno">Inferno</option>
            <option value="gray">Grayscale</option>
          </select>
          
          <div className="w-px h-6 bg-gray-300 mx-2" />
          
          {/* Zoom */}
          <button
            onClick={() => setZoom(z => Math.max(MIN_ZOOM, z - ZOOM_STEP))}
            disabled={disabled || zoom <= MIN_ZOOM}
            className="p-2 text-gray-600 hover:bg-gray-200 rounded-lg disabled:opacity-50"
            title="Zoom Out"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <span className="text-xs text-gray-600 w-12 text-center">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => setZoom(z => Math.min(MAX_ZOOM, z + ZOOM_STEP))}
            disabled={disabled || zoom >= MAX_ZOOM}
            className="p-2 text-gray-600 hover:bg-gray-200 rounded-lg disabled:opacity-50"
            title="Zoom In"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          
          <div className="w-px h-6 bg-gray-300 mx-2" />
          
          {/* Export/Save */}
          <button
            onClick={handleExport}
            disabled={disabled}
            className="p-2 text-gray-600 hover:bg-gray-200 rounded-lg disabled:opacity-50"
            title="Export as PNG"
          >
            <Download className="h-4 w-4" />
          </button>
          {onSave && (
            <button
              onClick={handleSave}
              disabled={disabled}
              className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg disabled:opacity-50"
              title="Save Changes"
            >
              <Save className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
      
      {/* Canvas Container */}
      <div 
        ref={containerRef}
        className="relative bg-gray-800 rounded-lg overflow-hidden"
        style={{ 
          width: width * zoom, 
          height: height * zoom,
          maxWidth: '100%',
          margin: '0 auto'
        }}
      >
        {/* Main Canvas */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 cursor-crosshair"
          style={{
            width: width * zoom,
            height: height * zoom,
            imageRendering: zoom > 1 ? 'pixelated' : 'auto',
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
        />
        
        {/* Overlay Canvas for cursor */}
        <canvas
          ref={overlayCanvasRef}
          className="absolute inset-0 pointer-events-none"
          style={{
            width: width * zoom,
            height: height * zoom,
          }}
        />
        
        {/* Disabled Overlay */}
        {disabled && (
          <div className="absolute inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center">
            <span className="text-white text-lg">Editor Disabled</span>
          </div>
        )}
      </div>
      
      {/* Status Bar */}
      <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
        <div className="flex items-center gap-4">
          <span>Tool: {tool === 'brush' ? 'Brush' : 'Eraser'}</span>
          <span>
            {cursorPos 
              ? `Position: ${Math.round(cursorPos.x)}, ${Math.round(cursorPos.y)}`
              : 'Position: -'
            }
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span>History: {historyIndex + 1}/{history.length}</span>
          <span>
            Press [ and ] to adjust brush size
          </span>
        </div>
      </div>
    </div>
  );
}

export default DepthValidationEditor;
