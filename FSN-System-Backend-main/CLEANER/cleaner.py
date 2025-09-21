import os
import random
from PIL import Image, ImageEnhance
import pillow_heif

# Register HEIF opener
pillow_heif.register_heif_opener()

# --- Configuration ---
# Directory containing the original images
INPUT_DIR = "input"
# Directory to save the processed images
OUTPUT_DIR = "output"
# Maximum brightness adjustment (e.g., 0.2 means +/- 20%)
BRIGHTNESS_MAX_CHANGE = 0.2
# Maximum rotation in degrees
ROTATION_MAX_CHANGE = 3.0
# Maximum contrast adjustment (e.g., 0.2 means +/- 20%)
CONTRAST_MAX_CHANGE = 0.2

def clean_metadata_and_modify_image(image_path, output_path):
    """
    Cleans metadata from an image, applies slight modifications, and saves it.
    """
    try:
        with Image.open(image_path) as img:
            # 1. Clean Metadata
            # By creating a new image and saving it without the exif data,
            # we effectively strip the metadata.
            data = list(img.getdata())
            image_without_metadata = Image.new(img.mode, img.size)
            image_without_metadata.putdata(data)

            # 2. Apply slight brightness change
            enhancer = ImageEnhance.Brightness(image_without_metadata)
            brightness_factor = 1.0 + random.uniform(-BRIGHTNESS_MAX_CHANGE, BRIGHTNESS_MAX_CHANGE)
            img_modified = enhancer.enhance(brightness_factor)

            # 3. Apply slight contrast change
            enhancer = ImageEnhance.Contrast(img_modified)
            contrast_factor = 1.0 + random.uniform(-CONTRAST_MAX_CHANGE, CONTRAST_MAX_CHANGE)
            img_modified = enhancer.enhance(contrast_factor)

            # Save the new image, ensuring it's in RGB mode for JPEG saving
            if img_modified.mode != 'RGB':
                img_modified = img_modified.convert('RGB')
            img_modified.save(output_path, "JPEG")
            print(f"Successfully processed and saved: {output_path}")

    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def main():
    """
    Main function to process all images in the input directory.
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    # Create input directory if it doesn't exist
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"Created directory: {INPUT_DIR}")
        print(f"Please add your images to the '{INPUT_DIR}' directory and run the script again.")
        return

    # Get list of images in the input directory
    try:
        image_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.heic'))]
    except FileNotFoundError:
        print(f"Error: Input directory '{INPUT_DIR}' not found.")
        return
        
    if not image_files:
        print(f"No images found in '{INPUT_DIR}'. Please add images and run again.")
        return

    print(f"Found {len(image_files)} images to process.")

    # Process each image
    for image_name in image_files:
        image_path = os.path.join(INPUT_DIR, image_name)
        base_name, extension = os.path.splitext(image_name)

        # Process each image 15 times
        for i in range(200):
            # Ensure the output is always a .jpg file
            output_name = f"{base_name}_cleaned_{i+1}.jpg"
            output_path = os.path.join(OUTPUT_DIR, output_name)
            clean_metadata_and_modify_image(image_path, output_path)

if __name__ == "__main__":
    print("--- Image Metadata Cleaner and Modifier ---")
    main()
