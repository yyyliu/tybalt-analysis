from PIL import Image
import os

h = 28

for f in os.listdir('.'):
  name, ext = os.path.splitext(f)
  if ext == '.png':
    print(f)
    img = Image.open(f)
    p = h / float(img.size[1])
    w = int(float(img.size[0]) * float(p))
    img = img.resize((w, h), Image.ANTIALIAS)
    img.save('./resized/{}'.format(f))
