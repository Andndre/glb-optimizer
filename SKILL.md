---
name: glb-optimizer
description: Optimizes 3D models (GLB/glTF) with Draco mesh compression, WebP texture downscaling (gltf.report pipeline), and exports Apple iOS AR Quick Look compliant USDZ files using headless Blender. Triggers on "compress glb", "convert usdz", "optimize 3d", "ar quick look", "gltf.report", "kompres glb".
---

# 3D Model (GLB & USDZ) Optimizer & Converter

A cross-platform skill and CLI toolkit to automate 3D model optimization (.glb / .gltf) for Web/Android deployment and export Apple-compliant `.usdz` archives for iOS AR Quick Look.

## Capabilities
1. **GLB Compression (Web / Android)**:
   - Full `gltf-transform` pipeline: deduplication, instance generation, palette texture merging, mesh flattening, welding, simplification, resampling, and pruning.
   - Textures compressed to WebP (default max: 1024px).
   - Geometry compressed with Google Draco (typically 85% to 98% file size reduction).
2. **USDZ Conversion (Apple iOS AR Quick Look)**:
   - Decodes Draco geometry into uncompressed vertices (required by Apple RealityKit).
   - Converts WebP textures into pure PNG (Apple Quick Look renders black or fails if WebP is present in USDZ).
   - Exports 64-byte aligned USDZ with official `UsdPreviewSurface` material shaders via Blender headless.

---

## Technical Constraints (Apple AR Quick Look)

> [!IMPORTANT]
> Apple iOS AR Quick Look strictly rejects standard web glTF optimizations:
> 1. **NO Draco Compression**: RealityKit does not support Draco decompression. Geometry in `.usdz` MUST be uncompressed vertex streams.
> 2. **NO WebP Textures**: iOS AR Quick Look fails or renders black textures if WebP is inside `.usdz`. Textures MUST be **PNG** or **JPEG**.
> 3. **UsdPreviewSurface**: Materials must use standard `UsdPreviewSurface` shaders.
>
> The included script (`scripts/glb_optimizer.py`) automatically de-dracos and converts WebP to PNG before handing off to Blender headless.

---

## System Requirements

The agent or user executing this skill must have the following tools installed:
- **Python 3.9+** (or `uv run python`)
- **Node.js & npx** (for `@gltf-transform/cli`)
- **Blender 4.2+ or 5.x** (auto-detected on Windows, macOS, and Linux, or configured via `--blender-path` / `BLENDER_PATH` environment variable)

---

## Agent Usage Instructions

When a user asks to optimize, compress, or convert 3D models:

### 1. Optimize GLB & Generate USDZ Simultaneously
```bash
python <path-to-skill>/scripts/glb_optimizer.py "<target-path>" --out-folder converted --usdz
```

### 2. Compress GLB Only (Web / Android)
```bash
python <path-to-skill>/scripts/glb_optimizer.py "<target-path>" --out-folder compressed
```

### 3. Convert to USDZ Only (Without GLB Recompression)
```bash
python <path-to-skill>/scripts/glb_optimizer.py "<target-path>" --out-folder usdz_out --usdz-only
```

### 4. Custom Texture Size & Suffix
```bash
python <path-to-skill>/scripts/glb_optimizer.py "<target-path>" --texture-size 2048 --suffix "_opt" --usdz
```

### 5. Reporting
Always output a clean markdown summary table showing:
- Original file names & sizes
- Optimized GLB sizes & reduction percentage
- Exported USDZ sizes
