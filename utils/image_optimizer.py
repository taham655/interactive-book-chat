from PIL import Image
import os

def optimize_image(image_path, output_path=None, sizes=[300, 600, 900], quality=85):
    """
    Optimize an image and create multiple sizes for responsive loading.
    
    Args:
        image_path: Path to the original image
        output_path: Base path for optimized images (optional)
        sizes: List of widths to generate
        quality: JPEG quality (1-100)
    
    Returns:
        List of dictionaries containing path and width for each generated image
    """
    if not output_path:
        directory = os.path.dirname(image_path)
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(directory, name)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Open and process image
    with Image.open(image_path) as img:
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        aspect_ratio = img.height / img.width
        outputs = []
        
        # Generate different sizes
        for width in sizes:
            height = int(width * aspect_ratio)
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Generate output path for this size
            size_path = f"{output_path}_{width}w.jpg"
            
            # Save optimized version
            resized.save(
                size_path,
                'JPEG',
                quality=quality,
                optimize=True
            )
            
            outputs.append({
                'path': size_path,
                'width': width
            })
            
        return outputs

def get_image_dimensions(image_path):
    """Get the dimensions of an image."""
    with Image.open(image_path) as img:
        return img.size
