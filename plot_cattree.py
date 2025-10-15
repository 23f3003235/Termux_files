from PIL import Image, ImageDraw, ImageFont

# Read the summary text
with open('cattree.txt', 'r') as f:
    lines = f.readlines()

# Prepare font/size and image dimensions
font = ImageFont.load_default()
width = max([font.getlength(line.rstrip()) for line in lines]) + 40
height = 18 * len(lines) + 40

img = Image.new("RGB", (int(width), int(height)), "white")
draw = ImageDraw.Draw(img)

y = 20
for line in lines:
    draw.text((20, y), line.rstrip(), font=font, fill=(25,25,25))
    y += 18

img.save("/data/data/com.termux/files/home/termux_files/reports/cattree.png")

