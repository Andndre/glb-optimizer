import bpy
import sys
import os

def main():
    try:
        args = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        print("Error: No arguments passed after '--'")
        sys.exit(1)

    if len(args) < 2:
        print("Usage: blender --background --python gltf_to_usdz.py -- <input_glb> <output_usdz> [downscale_size]")
        sys.exit(1)

    input_path = os.path.abspath(args[0])
    output_path = os.path.abspath(args[1])
    downscale = args[2] if len(args) > 2 else "1024"

    # Reset scene to empty
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Import GLB
    bpy.ops.import_scene.gltf(filepath=input_path)

    # Export kwargs for Apple AR Quick Look USDZ
    export_kwargs = {
        "filepath": output_path,
        "generate_preview_surface": True,
        "export_materials": True,
    }
    if downscale in ["256", "512", "1024", "2048", "4096"]:
        export_kwargs["usdz_downscale_size"] = downscale

    bpy.ops.wm.usd_export(**export_kwargs)
    print("SUCCESS_USDZ_EXPORT")

if __name__ == "__main__":
    main()
