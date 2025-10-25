#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pillow>=10.0.0",
# ]
# ///
"""Generate icon set for Thai ID Card Reader Chrome extension."""

from PIL import Image, ImageDraw
import os

def create_icon(size):
    """
    Create an icon representing a Thai ID card.

    Args:
        size: Icon size (width and height in pixels)
    """
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Calculate dimensions based on size
    margin = size // 8
    card_width = size - (2 * margin)
    card_height = int(card_width * 0.63)  # ID card aspect ratio

    # Center the card vertically
    card_y = (size - card_height) // 2

    # Draw card background (gradient effect with layers)
    card_rect = [margin, card_y, margin + card_width, card_y + card_height]

    # Shadow for depth
    shadow_offset = max(2, size // 32)
    shadow_rect = [
        card_rect[0] + shadow_offset,
        card_rect[1] + shadow_offset,
        card_rect[2] + shadow_offset,
        card_rect[3] + shadow_offset
    ]
    draw.rounded_rectangle(shadow_rect, radius=size//16, fill=(0, 0, 0, 60))

    # Card base - gradient blue
    draw.rounded_rectangle(card_rect, radius=size//16, fill=(75, 110, 175, 255))

    # Thai flag stripe (red-white-blue)
    stripe_height = max(2, card_height // 8)
    stripe_y = card_y + max(2, size // 20)

    # Red stripe
    draw.rectangle(
        [margin + max(1, size//32), stripe_y,
         margin + card_width - max(1, size//32), stripe_y + stripe_height],
        fill=(237, 28, 36, 255)
    )

    # White stripe
    draw.rectangle(
        [margin + max(1, size//32), stripe_y + stripe_height,
         margin + card_width - max(1, size//32), stripe_y + 2*stripe_height],
        fill=(255, 255, 255, 255)
    )

    # Blue stripe
    draw.rectangle(
        [margin + max(1, size//32), stripe_y + 2*stripe_height,
         margin + card_width - max(1, size//32), stripe_y + 3*stripe_height],
        fill=(45, 42, 115, 255)
    )

    # Person icon silhouette (simplified)
    if size >= 32:
        person_x = margin + card_width // 5
        person_y = card_y + card_height // 2
        head_radius = max(3, size // 20)

        # Head
        draw.ellipse(
            [person_x - head_radius, person_y - head_radius,
             person_x + head_radius, person_y + head_radius],
            fill=(255, 255, 255, 200)
        )

        # Body (simplified rectangle)
        body_width = head_radius * 2
        body_height = int(head_radius * 1.5)
        draw.rounded_rectangle(
            [person_x - body_width//2, person_y + head_radius,
             person_x + body_width//2, person_y + head_radius + body_height],
            radius=max(1, size//40),
            fill=(255, 255, 255, 200)
        )

    # Text lines representing card data (if size is large enough)
    if size >= 48:
        line_x = margin + card_width // 2 + max(2, size // 32)
        line_start_y = card_y + card_height // 2 - max(2, size // 32)
        line_width = card_width // 3
        line_height = max(2, size // 32)
        line_spacing = max(3, size // 20)

        # Draw 3-4 lines representing text
        num_lines = 3 if size < 64 else 4
        for i in range(num_lines):
            y_pos = line_start_y + (i * line_spacing)
            # Vary line widths slightly
            width_factor = 0.9 if i % 2 == 0 else 1.0
            draw.rounded_rectangle(
                [line_x, y_pos,
                 line_x + int(line_width * width_factor), y_pos + line_height],
                radius=max(1, size//64),
                fill=(255, 255, 255, 180)
            )

    return img


def main():
    """Generate all icon sizes."""
    # Create icons directory if it doesn't exist
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    os.makedirs(icons_dir, exist_ok=True)

    # Generate icons at different sizes
    sizes = [16, 48, 128]

    for size in sizes:
        print(f"Generating {size}x{size} icon...")
        icon = create_icon(size)

        # Save the icon
        icon_path = os.path.join(icons_dir, f'icon{size}.png')
        icon.save(icon_path, 'PNG')
        print(f"  Saved: {icon_path}")

    print("\n✓ All icons generated successfully!")


if __name__ == '__main__':
    main()
