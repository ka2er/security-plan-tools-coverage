import yaml
from PIL import Image, ImageDraw, ImageFont
import os
import platform

# COLOR Group Colors
COLOR_BLUE = (0, 91, 172)
COLOR_YELLOW = (255, 199, 44)
COLOR_WHITE = (255, 255, 255)
COLORS = [
    "#36a9e1",
    "#76b82a",
    "#f9b233",
    "#e6007e",
    "#82358c",
    "#c8d300",
    "#e6332a"
]

# Convert hex to RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Calculate contrasting text color
def get_contrast_color(bg_color):
    luminance = (0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]) / 255
    return (0, 0, 0) if luminance > 0.5 else (255, 255, 255)

# Darken color based on intensity
def darken_color(color, intensity):
    return tuple(max(0, min(255, int(c * intensity))) for c in color)

# Split text into lines that fit within width
def split_text_into_lines(text, max_width, font, draw):
    words = text.split()
    lines = []
    current_line = words[0]
    
    for word in words[1:]:
        test_line = current_line + " " + word
        test_width = draw.textlength(test_line, font=font)
        if test_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

# Create rotated text image
def create_rotated_text_image(text, font, text_color):
    # First create an image for the text
    text_width = max(font.getlength(line) for line in text)
    line_height = font.size + 2
    text_height = len(text) * line_height
    
    text_img = Image.new('RGBA', (int(text_width), int(text_height)), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    
    # Draw each line of text
    for i, line in enumerate(text):
        text_draw.text((0, i * line_height), line, fill=text_color, font=font)
    
    # Rotate the image
    rotated = text_img.rotate(90, expand=True)
    return rotated

# Load YAML file
def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Generate landscape image
def generate_image(data, output_path):
    # Image dimensions (1080p landscape)
    width = 1920
    height = 1080
    image = Image.new('RGB', (width, height), COLOR_WHITE)
    draw = ImageDraw.Draw(image)

    # Define margins and dimensions
    margin = 30
    header_height = 100  # Increased header height
    legend_width = 50  # Width for vertical text
    domain_header_height = 40  # Separate height for domain names

    # Define layer positions
    layers = data['cyber_program']['layers']
    domains = data['cyber_program']['domains']
    num_layers = len(layers)
    num_domains = len(domains)

    # Calculate main area dimensions
    main_width = width - margin * 2 - legend_width
    main_height = height - margin * 2 - header_height

    # Calculate cell dimensions
    cell_width = main_width / num_domains
    cell_height = main_height / num_layers

    # Determine the operating system
    system = platform.system()

    # Load the appropriate font based on the OS
    if system == "Darwin":  # macOS
        header_font = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 24)
        domain_font = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 18)
        layer_font = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 14)
        content_font = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 12)
    elif system == "Windows":  # Windows
        header_font = ImageFont.truetype("arial.ttf", 24)
        domain_font = ImageFont.truetype("arial.ttf", 18)
        layer_font = ImageFont.truetype("arial.ttf", 14)
        content_font = ImageFont.truetype("arial.ttf", 12)
    else:  # Linux or other
        header_font = ImageFont.load_default()
        domain_font = ImageFont.load_default()
        layer_font = ImageFont.load_default()
        content_font = ImageFont.load_default()


    # Draw main header
    header_x1 = margin
    header_y1 = margin
    header_x2 = width - margin - legend_width
    header_y2 = margin + header_height - domain_header_height
    draw.rectangle([header_x1, header_y1, header_x2, header_y2], fill=COLOR_BLUE)
    
    # Draw domain header section
    domain_header_y1 = header_y2
    domain_header_y2 = margin + header_height
    draw.rectangle([header_x1, domain_header_y1, header_x2, domain_header_y2], fill=COLOR_BLUE)
    
    # Center title in main header
    title_text = "Cyber Security Landscape"
    title_bbox = draw.textbbox((0, 0), title_text, font=header_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = header_x1 + (header_x2 - header_x1 - title_width) / 2
    title_y = header_y1 + (header_y2 - header_y1 - (title_bbox[3] - title_bbox[1])) / 2
    draw.text((title_x, title_y), title_text, fill=COLOR_YELLOW, font=header_font)

    # Draw legend with vertical text
    legend_x1 = width - margin - legend_width
    legend_y1 = margin
    legend_x2 = width - margin
    legend_y2 = height - margin
    draw.rectangle([legend_x1, legend_y1, legend_x2, legend_y2], fill=COLOR_BLUE)

    # Calculate maximum number of items for intensity scaling
    max_items = 1
    for domain in domains:
        for layer in layers:
            entries = [entry for entry in domain['entries'] if entry['layer'] == layer['id']]
            item_count = sum(len(entry.get('controls', [])) + len(entry.get('tools', [])) 
                           for entry in entries)
            if item_count > max_items:
                max_items = item_count

    # Draw cells with domain colors
    for domain_idx, domain in enumerate(domains):
        base_color = hex_to_rgb(COLORS[domain_idx])
        
        # Draw domain name in header
        x = margin + domain_idx * cell_width + cell_width / 2
        y = domain_header_y1 + domain_header_height / 2
        
        # Calculate text width for domain name
        domain_bbox = draw.textbbox((0, 0), domain['name'], font=domain_font)
        domain_width = domain_bbox[2] - domain_bbox[0]
        
        # If domain name would overlap, split into multiple lines
        if domain_width > cell_width - 20:
            words = domain['name'].split()
            lines = []
            current_line = words[0]
            for word in words[1:]:
                test_line = current_line + " " + word
                test_width = draw.textlength(test_line, font=domain_font)
                if test_width <= cell_width - 20:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)
            
            # Draw multi-line domain name
            line_height = domain_bbox[3] - domain_bbox[1]
            start_y = y - (line_height * len(lines)) / 2
            for i, line in enumerate(lines):
                line_bbox = draw.textbbox((0, 0), line, font=domain_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = x - line_width / 2
                draw.text((line_x, start_y + i * line_height), line, 
                         fill=COLOR_WHITE, font=domain_font)
        else:
            # Draw single-line domain name
            draw.text((x, y), domain['name'], fill=COLOR_WHITE, 
                     font=domain_font, anchor="mm")
        
        for layer_idx, layer in enumerate(layers):
            # Calculate cell position
            x1 = margin + domain_idx * cell_width
            y1 = margin + header_height + layer_idx * cell_height
            x2 = x1 + cell_width
            y2 = y1 + cell_height
            
            # Find entries for this cell
            entries = [entry for entry in domain['entries'] if entry['layer'] == layer['id']]
            item_count = sum(len(entry.get('controls', [])) + len(entry.get('tools', [])) 
                           for entry in entries)
            
            # Calculate cell color based on content and ensure good contrast
            if item_count == 0:
                # Very light and transparent background for empty cells
                cell_color = (*base_color, 25)  # Low alpha value for high transparency
            else:
                # Adjust intensity based on content, ensuring minimum contrast
                intensity = max(0.4, 1.0 - (0.4 * (item_count / max_items)))
                cell_color = darken_color(base_color, intensity)
            
            text_color = get_contrast_color(cell_color)
            # Draw cell background
            draw.rectangle([x1, y1, x2, y2], fill=cell_color)

            # Draw content
            if entries:
                y_offset = y1 + 10
                for entry in entries:
                    # Draw tools
                    if 'tools' in entry:
                        tools = entry['tools'] if isinstance(entry['tools'], list) else [entry['tools']]
                        for tool in tools:
                            # Calculate text width
                            text = f"• {tool}"
                            text_width = draw.textlength(text, font=content_font)
                            available_width = x2 - x1 - 20  # Cell width minus margins
                            
                            if text_width > available_width:
                                # Split text into words
                                words = text.split()
                                line = words[0]
                                for word in words[1:]:
                                    test_line = line + " " + word
                                    test_width = draw.textlength(test_line, font=content_font)
                                    if test_width <= available_width:
                                        line = test_line
                                    else:
                                        draw.text((x1 + 10, y_offset), line, 
                                                fill=text_color, font=content_font)
                                        y_offset += 20
                                        line = word
                                draw.text((x1 + 10, y_offset), line, 
                                        fill=text_color, font=content_font)
                            else:
                                draw.text((x1 + 10, y_offset), text, 
                                        fill=text_color, font=content_font)
                            y_offset += 20
                    
                    # Draw controls
                    if 'controls' in entry:
                        controls = entry['controls'] if isinstance(entry['controls'], list) else [entry['controls']]
                        for control in controls:
                            # Calculate text width
                            text = f"• {control}"
                            text_width = draw.textlength(text, font=content_font)
                            available_width = x2 - x1 - 20  # Cell width minus margins
                            
                            if text_width > available_width:
                                # Split text into words
                                words = text.split()
                                line = words[0]
                                for word in words[1:]:
                                    test_line = line + " " + word
                                    test_width = draw.textlength(test_line, font=content_font)
                                    if test_width <= available_width:
                                        line = test_line
                                    else:
                                        draw.text((x1 + 10, y_offset), line, 
                                                fill=text_color, font=content_font)
                                        y_offset += 20
                                        line = word
                                draw.text((x1 + 10, y_offset), line, 
                                        fill=text_color, font=content_font)
                            else:
                                draw.text((x1 + 10, y_offset), text, 
                                        fill=text_color, font=content_font)
                            y_offset += 20
                    
                    # Draw images
                    if 'image' in entry:
                        image_names = entry['image'].split(',') if isinstance(entry['image'], str) else entry['image']
                        x_img = x1 + 10
                        max_height = 40  # Maximum height for images
                        max_width = 60   # Maximum width for images
                        spacing = 10  # Space between images
                        
                        for img_name in image_names:
                            img_name = img_name.strip() + ".png"
                            img_path = os.path.join('img', img_name)
                            
                            if os.path.exists(img_path):
                                try:
                                    img = Image.open(img_path)
                                    
                                    # Ensure image has alpha channel for transparency
                                    if img.mode != 'RGBA':
                                        img = img.convert('RGBA')
                                    
                                    # Get bounding box of non-transparent pixels
                                    bbox = img.getbbox()
                                    if bbox:
                                        img = img.crop(bbox)
                                    
                                    # Calculate new dimensions maintaining aspect ratio
                                    aspect_ratio = img.width / img.height
                                    if aspect_ratio > 1:  # Wider than tall
                                        new_width = min(max_width, img.width)
                                        new_height = int(new_width / aspect_ratio)
                                        if new_height > max_height:
                                            new_height = max_height
                                            new_width = int(new_height * aspect_ratio)
                                    else:  # Taller than wide
                                        new_height = min(max_height, img.height)
                                        new_width = int(new_height * aspect_ratio)
                                        if new_width > max_width:
                                            new_width = max_width
                                            new_height = int(new_width / aspect_ratio)
                                    
                                    # Resize image
                                    img = img.resize((int(new_width), int(new_height)), Image.Resampling.LANCZOS)
                                    
                                    # Check if image would exceed cell width
                                    if x_img + new_width > x2 - 10:
                                        # Move to next line
                                        x_img = x1 + 10
                                        y_offset += max_height + spacing
                                    
                                    # Ensure we don't exceed cell height
                                    if y_offset + new_height > y2 - 10:
                                        break  # Stop adding images if we would exceed cell height
                                    
                                    # Paste image with transparency
                                    image.paste(img, (int(x_img), int(y_offset)), img)
                                    x_img += new_width + spacing  # Move right for next image
                                    
                                except Exception as e:
                                    print(f"Error processing image {img_path}: {e}")
                            else:
                                print(f"Image not found: {img_path}")

    # Draw layer names in legend vertically
    for i, layer in enumerate(layers):
        # Calculate cell boundaries
        cell_y1 = margin + header_height + i * cell_height
        cell_y2 = cell_y1 + cell_height
        
        # Split layer name into lines if needed
        max_line_width = cell_height - 20  # Maximum width for vertical text (becomes height after rotation)
        lines = split_text_into_lines(layer['name'], max_line_width, layer_font, draw)
        
        # Create rotated text image with multiple lines
        rotated = create_rotated_text_image(lines, layer_font, COLOR_WHITE)
        
        # Calculate position (left-aligned, vertically centered on middle line)
        x = legend_x1 + 10  # Left alignment with padding
        
        # Calculate vertical position to center on middle line
        #text_height = rotated.width  # Width after rotation is original height
        #middle_line_offset = (len(lines) - 1) * (layer_font.size + 2) / 2
        #y = cell_y1 + (cell_height - text_height) / 2 + middle_line_offset
        #y = cell_y1
        
        # Paste rotated text
        #image.paste(rotated, (int(x), int(y)), rotated)
        image.paste(rotated, (int(x), int(cell_y1 + 10)), rotated)
        
        # Draw white separation line between legend entries
        if i < len(layers) - 1:
            line_y = cell_y2
            draw.line([(legend_x1, line_y), (legend_x2, line_y)], fill=COLOR_WHITE, width=1)

    # Save the image
    image.save(output_path)

# Main function
def main():
    data = load_yaml('config/cyber.yaml')
    generate_image(data, 'output.png')

if __name__ == '__main__':
    main()
