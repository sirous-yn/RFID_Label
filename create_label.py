from PIL import Image, ImageDraw, ImageFont
from datetime import date

# Label information
pid = "PMT-0042"
today = date.today().strftime("%Y-%m-%d")

# 4 × 2 inch label at 300 DPI
width = 1200
height = 600

# Create a white label
image = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(image)

# Fonts
#font = ImageFont.truetype("DejaVuSans.ttf", 60)
#small_font = ImageFont.truetype("DejaVuSans.ttf", 45)

font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 60)
small_font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 45)

# Write the information
draw.text((80, 70), "RFID COMPONENT", fill="black", font=font)
draw.text((80, 220), f"PID: {pid}", fill="black", font=small_font)
draw.text((80, 320), f"Date: {today}", fill="black", font=small_font)

# Save the label
image.save("label.png")

print("Label created successfully!")
print(f"PID: {pid}")
print(f"Date: {today}")