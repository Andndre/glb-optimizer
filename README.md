# GLB Optimizer & Apple USDZ Converter

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Skills.sh](https://img.shields.io/badge/skills.sh-indexed-success.svg)](https://skills.sh)

A cross-platform [Agent Skill](https://skills.sh) and standalone CLI to compress 3D models (`.glb` / `.gltf`) for Web/Android and convert them to Apple-compliant `.usdz` archives for iOS AR Quick Look.

---

## ⚡ Features

- **Extreme File Size Reduction (-80% to -98%)**: Uses `@gltf-transform` to run mesh simplification, deduplication, welding, Draco mesh compression, and WebP 1024px downscaling.
- **Apple iOS AR Quick Look Compliant**: Automatically resolves Apple's strict constraints by decoding Draco back to uncompressed vertex buffers and converting WebP textures to pure PNG with `UsdPreviewSurface` materials via Blender 5.x / 4.x headless.
- **Zero Python Dependencies**: Written entirely in pure Python 3 standard library (no `pip install` required).
- **Cross-Platform**: Tested and works seamlessly on Windows, macOS, and Linux.
- **Agent Skill Ready**: Compatible with `skills.sh`, Claude Code, Cursor, Codex, Antigravity, and GitHub Copilot agents.

---

## 📦 Installation as an Agent Skill

Install this skill directly into your AI coding agent workspace using `npx skills`:

```bash
npx skills add Andndre/glb-optimizer
```

Once installed, your AI agent will automatically detect and execute optimization workflows whenever you ask to compress 3D models or prepare assets for iOS AR Quick Look.

---

## 🛠️ Prerequisites

To run the optimization pipeline, your system must have:

1. **Python 3.9+** (or [`uv`](https://docs.astral.sh/uv/))
2. **Node.js & npx** (used to run `@gltf-transform/cli` on demand):
   ```bash
   node -v
   npx -v
   ```
3. **Blender (4.2+ or 5.x)**:
   - **Windows**: Auto-detected from `C:\Program Files\Blender Foundation\`
   - **macOS**: Auto-detected from `/Applications/Blender.app`
   - **Linux**: Auto-detected from `/usr/bin/blender` or flatpak/snap
   *(Or specify manually using `--blender-path` or `export BLENDER_PATH=...`)*

---

## 🚀 Standalone CLI Usage

You can also use the script directly from your terminal:

### 1. Optimize GLB and Export USDZ Simultaneously
```bash
python scripts/glb_optimizer.py "path/to/models" --out-folder converted --usdz
```

### 2. Compress GLBs Only (Web / Android)
```bash
python scripts/glb_optimizer.py "path/to/models" --out-folder compressed
```

### 3. Convert Existing GLBs to Apple USDZ Only
```bash
python scripts/glb_optimizer.py "path/to/models" --out-folder usdz_out --usdz-only
```

### 4. Custom Parameters
```bash
python scripts/glb_optimizer.py "model.glb" --texture-size 2048 --suffix "_opt" --usdz
```

### CLI Arguments

| Argument | Description | Default |
| :--- | :--- | :---: |
| `path` | Path to a `.glb` file or folder containing `.glb` files | `.` (current dir) |
| `-o, --out-folder` | Subfolder or directory path to save outputs | `compressed` |
| `-s, --suffix` | Suffix appended before the extension | `_v1` |
| `-t, --texture-size` | Maximum texture resolution in pixels | `1024` |
| `--usdz` | Export Apple iOS AR Quick Look `.usdz` | `False` |
| `--usdz-only` | Only convert to `.usdz` without GLB optimization | `False` |
| `--no-draco` | Disable Draco geometry compression | `False` |
| `--no-clean-space` | Preserve whitespaces in filenames | `False` |
| `--blender-path` | Manual path to Blender executable | *Auto-detected* |

---

## 🍎 Technical Note: Why Apple AR Quick Look Needs Special Treatment

Apple's RealityKit and AR Quick Look have strict requirements that standard web-optimized glTF models violate:

1. **Draco Geometry**: Apple devices cannot decode Google Draco compression inside USDZ containers. Models with Draco will fail to load or crash AR Quick Look.
2. **WebP Textures**: WebP is not supported inside USDZ by iOS AR Quick Look; textures render as pitch black. They must be pure PNG or JPEG.
3. **Material Shaders**: RealityKit requires `UsdPreviewSurface` shader nodes.

`glb-optimizer` handles these requirements by performing intermediate geometry decoding and PNG transcoding before packaging the USDZ file via Blender headless.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
