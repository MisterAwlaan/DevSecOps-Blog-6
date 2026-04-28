import fitz
import sys
import os

doc = fitz.open(sys.argv[1])
for i in range(len(doc)):
    page = doc[i]
    images = page.get_images(full=True)
    if images:
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            image_path = f"page_{i+1}_img_{img_index+1}.{ext}"
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            print(f"Saved {image_path}")
