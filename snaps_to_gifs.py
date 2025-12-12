from PIL import Image
import glob
import os

def create_gif_from_pngs(output_filename, png_dir, duration=100, loop=0):
    """
    Save the images as a GIF.
    
    args:
      output_filename: Name of the output GIF file.
      png_dir: Directory containing the PNG files.
      duration: Duration between frames in milliseconds.
      loop: Number of loops for the GIF (0 means infinite).
    """
    files = glob.glob(f"{png_dir}/*.png")
    files = sorted(files, key=lambda f: int(os.path.basename(f).split("_")[1])) # order by episode number

    if not files:
        print("No PNG files found in the specified directory.")
        return

    # Open the first image and append the rest
    images = [Image.open(file) for file in files]
    
    images[0].save(
        output_filename,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=loop
    )
    print(f"GIF successfully created: {output_filename}")

if __name__ == "__main__":
    create_gif_from_pngs("evolution.gif", "evolution_snaps", duration=500,loop=0)
    create_gif_from_pngs("qdiffs.gif", "diff_heatmap_snaps", duration=500,loop=0)