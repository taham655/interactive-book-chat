from PIL import Image
import os

def generate_responsive_images(original_image_path, output_dir):
    """Generate responsive images at different sizes."""
    sizes = [200, 400, 800]  # Width in pixels for different device sizes
    image_paths = {}
    
    try:
        with Image.open(original_image_path) as img:
            filename = os.path.basename(original_image_path)
            name, ext = os.path.splitext(filename)
            
            # Generate images at different sizes
            for size in sizes:
                # Calculate height maintaining aspect ratio
                ratio = size / float(img.size[0])
                height = int(float(img.size[1]) * ratio)
                
                resized = img.resize((size, height), Image.Resampling.LANCZOS)
                output_path = os.path.join(output_dir, f"{name}-{size}w{ext}")
                resized.save(output_path, quality=85, optimize=True)
                image_paths[size] = output_path
                
    except Exception as e:
        print(f"Error processing image: {e}")
        return None
        
    return image_paths

def get_image_dimensions(image_path):
    """Get image dimensions for proper scaling."""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception:
        return None
