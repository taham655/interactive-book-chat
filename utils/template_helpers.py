def responsive_image(image_path, alt_text, class_name=None, sizes=None):
    """
    Generate responsive image HTML markup.
    
    Args:
        image_path: Base path to the image (without size suffix)
        alt_text: Alternative text for the image
        class_name: Optional CSS class name
        sizes: Optional sizes attribute value
    
    Returns:
        HTML markup for responsive image
    """
    if sizes is None:
        sizes = "(max-width: 300px) 300px, (max-width: 600px) 600px, 900px"
    
    # Generate srcset
    widths = [300, 600, 900]
    srcset_items = [
        f"{image_path}_{width}w.jpg {width}w"
        for width in widths
    ]
    srcset = ", ".join(srcset_items)
    
    # Generate class attribute if provided
    class_attr = f' class="{class_name}"' if class_name else ''
    
    return f'''
        <img src="{image_path}_600w.jpg" 
             srcset="{srcset}"
             sizes="{sizes}"
             alt="{alt_text}"{class_attr}
             loading="lazy"
        >
    '''.strip()
