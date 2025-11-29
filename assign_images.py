#!/usr/bin/env python
"""
Script to assign images to products before starting the server.
Place your images in media/produtos/ folder with filenames matching the product names.
"""
import os
import django
import unicodedata

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quitute_nas_nuvens.settings')
django.setup()

from consumidor.models import Item

# Map product NAMES (from PRODUTOS_PADARIA) to image filenames found in media/produtos
# This script will try to match items by name (case- and accent-insensitive) and assign
# the corresponding image path relative to MEDIA_ROOT (upload_to='produtos/').
PRODUCT_IMAGES_BY_NAME = {
    'pão francês': 'pao-frances.jpg',
    'croissant': 'croissant.jpg',
    'pao careca': 'pao-careca.jpg',
    'brioche': 'brioche.jpg',
    'pao de queijo': 'pao-de-queijo.jpg',
    'joelho': 'joelho.jpg',
    'coxinha': 'coxinha.jpg',
    'sonho': 'sonho.jpeg',
    'bolo de chocolate': 'bolo-de-chocolate.jpg',
    'bolo de cenoura': 'bolo-de-cenoura.jpg',
    'torta de limao': 'torta-de-limao.jpg',
    'cookie de chocolate': 'cookie.jpg',
    'brigadeiro gigante': 'brigadeiro-gigante.jpg',
    'cheesecake': 'cheesecake.jpg',
    'muffin quentinho': 'muffin-quentinho.jpg',
    'empada': 'empada.jpg',
    'quiche': 'quiche.jpg',
    'pão doce': 'pao-doce.jpg',
    'torta de maçã': 'torta-de-maca.jpg',
    'brownie': 'brownie.jpg',
}

def normalize_text(s: str) -> str:
    if not s:
        return ''
    s = s.lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    # remove non-alphanumeric characters
    s = ''.join(ch for ch in s if ch.isalnum())
    return s

def assign_images():
    """Assign images to products"""
    updated = 0
    not_found = 0

    for item_name, filename in PRODUCT_IMAGES_BY_NAME.items():
        image_path = f'produtos/{filename}'
        try:
            item = Item.objects.get(nome=item_name)
            item.imagem = image_path
            item.save()
            print(f"✓ Updated {item.nome} with image {filename}")
            updated += 1
        except Item.DoesNotExist:
            # Create the item if it doesn't exist locally, then assign the image
            item = Item.objects.create(nome=item_name, quantidade_estoque=0, disponivel=False, imagem=image_path)
            print(f"☆ Created and assigned image for new product {item.nome}")
            updated += 1

    print(f"\nSummary: {updated} updated, {not_found} not found")

if __name__ == '__main__':
    print("Assigning images to products...\n")
    assign_images()
    print("\nDone! You can now start the server.")
