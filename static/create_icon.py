"""
Create a simple robot icon for ReAct Nexus
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with a transparent background
size = (256, 256)
image = Image.new('RGBA', size, (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Draw a robot face
# Head
draw.rectangle([(48, 48), (208, 208)], fill=(52, 152, 219), outline=(41, 128, 185), width=5)

# Eyes
draw.ellipse([(80, 90), (120, 130)], fill=(255, 255, 255), outline=(0, 0, 0), width=3)
draw.ellipse([(136, 90), (176, 130)], fill=(255, 255, 255), outline=(0, 0, 0), width=3)
draw.ellipse([(90, 100), (110, 120)], fill=(0, 0, 0))
draw.ellipse([(146, 100), (166, 120)], fill=(0, 0, 0))

# Mouth
draw.rectangle([(90, 160), (166, 180)], fill=(255, 255, 255), outline=(0, 0, 0), width=3)
draw.line([(90, 170), (166, 170)], fill=(0, 0, 0), width=3)
draw.line([(110, 160), (110, 180)], fill=(0, 0, 0), width=3)
draw.line([(130, 160), (130, 180)], fill=(0, 0, 0), width=3)
draw.line([(150, 160), (150, 180)], fill=(0, 0, 0), width=3)

# Antenna
draw.rectangle([(118, 20), (138, 48)], fill=(231, 76, 60), outline=(192, 57, 43), width=3)
draw.ellipse([(118, 10), (138, 30)], fill=(231, 76, 60), outline=(192, 57, 43), width=3)

# Save as PNG first
png_path = os.path.join(os.path.dirname(__file__), 'robot_icon.png')
image.save(png_path)

# Convert to ICO
ico_path = os.path.join(os.path.dirname(__file__), 'robot_icon.ico')
image.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

print(f"Icon created successfully at {ico_path}")
