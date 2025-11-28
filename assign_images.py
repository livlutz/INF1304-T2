#!/usr/bin/env python
"""
Script to assign images to products before starting the server.
Place your images in media/produtos/ folder with filenames matching the product names.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quitute_nas_nuvens.settings')
django.setup()

from consumidor.models import Item

# Map product IDs to image filenames
# Update these filenames to match your actual image files
PRODUCT_IMAGES = {
    1: 'pao-frances.jpg',
    2: 'croissant.jpg',
    3: 'pao-careca.jpg',
    4: 'brioche.jpg',
    5: 'pao-de-queijo.jpg',
    6: 'joelho.jpg',
    7: 'coxinha.jpg',
    8: 'sonho.jpg',
    9: 'bolo-chocolate.jpg',
    10: 'bolo-cenoura.jpg',
    11: 'torta-limao.jpg',
    12: 'cookie-chocolate.jpg',
    13: 'brigadeiro-gigante.jpg',
    14: 'cheesecake.jpg',
    15: 'muffin.jpg',
    16: 'empada.jpg',
    17: 'quiche.jpg',
    18: 'pao-doce.jpg',
    19: 'torta-maca.jpg',
    20: 'brownie.jpg',
}

def assign_images():
    """Assign images to products"""
    updated = 0
    not_found = 0

    for item_id, filename in PRODUCT_IMAGES.items():
        try:
            item = Item.objects.get(id=item_id)
            image_path = f'media/produtos/{filename}'
            item.imagem = image_path
            item.save()
            print(f"✓ Updated {item.nome} with image {filename}")
            updated += 1
        except Item.DoesNotExist:
            print(f"✗ Product with ID {item_id} not found")
            not_found += 1

    print(f"\nSummary: {updated} updated, {not_found} not found")

if __name__ == '__main__':
    print("Assigning images to products...\n")
    assign_images()
    print("\nDone! You can now start the server.")
