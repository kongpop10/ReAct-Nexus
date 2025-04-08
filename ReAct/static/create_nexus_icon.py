"""
Create a Nexus-themed icon for ReAct Nexus
Represents a network hub/connection point with nodes and connections
"""
from PIL import Image, ImageDraw
import os
import math

# Create a new image with a transparent background
size = (256, 256)
image = Image.new('RGBA', size, (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Colors
primary_color = (41, 128, 185)  # Blue
secondary_color = (52, 152, 219)  # Lighter blue
highlight_color = (231, 76, 60)  # Red
node_color = (236, 240, 241)  # Light gray
background_color = (44, 62, 80, 200)  # Dark blue with transparency

# Draw a circular background
draw.ellipse([(28, 28), (228, 228)], fill=background_color, outline=primary_color, width=3)

# Center point
center = (128, 128)

# Draw the central node (larger)
central_node_radius = 25
draw.ellipse(
    [(center[0] - central_node_radius, center[1] - central_node_radius), 
     (center[0] + central_node_radius, center[1] + central_node_radius)], 
    fill=highlight_color, outline=(0, 0, 0), width=2
)

# Draw outer nodes and connections
num_nodes = 6
node_radius = 15
orbit_radius = 80

for i in range(num_nodes):
    # Calculate node position
    angle = 2 * math.pi * i / num_nodes
    x = center[0] + orbit_radius * math.cos(angle)
    y = center[1] + orbit_radius * math.sin(angle)
    
    # Draw connection line
    draw.line([(center[0], center[1]), (x, y)], fill=secondary_color, width=4)
    
    # Draw node
    draw.ellipse(
        [(x - node_radius, y - node_radius), (x + node_radius, y + node_radius)], 
        fill=node_color, outline=primary_color, width=2
    )

# Draw some connecting lines between outer nodes to form a network
for i in range(num_nodes):
    angle1 = 2 * math.pi * i / num_nodes
    x1 = center[0] + orbit_radius * math.cos(angle1)
    y1 = center[1] + orbit_radius * math.sin(angle1)
    
    # Connect to two adjacent nodes
    for offset in [1, 2]:
        j = (i + offset) % num_nodes
        angle2 = 2 * math.pi * j / num_nodes
        x2 = center[0] + orbit_radius * math.cos(angle2)
        y2 = center[1] + orbit_radius * math.sin(angle2)
        
        # Draw a slightly curved line
        # Calculate control point for the curve (perpendicular to the line)
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Move the control point slightly away from the center
        ctrl_x = mid_x + (mid_x - center[0]) * 0.2
        ctrl_y = mid_y + (mid_y - center[1]) * 0.2
        
        # Draw the curved connection
        draw.line([(x1, y1), (ctrl_x, ctrl_y), (x2, y2)], fill=primary_color, width=2)

# Save as PNG first
png_path = os.path.join(os.path.dirname(__file__), 'nexus_icon.png')
image.save(png_path)

# Convert to ICO
ico_path = os.path.join(os.path.dirname(__file__), 'nexus_icon.ico')
image.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

print(f"Nexus icon created successfully at {ico_path}")
