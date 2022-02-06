import pyokaganutils as pyoka
import matplotlib.pyplot as plt

from numpy import array
from zlib import decompress

f = open('..\\resources\\basn6a08.png', 'rb')

PngSignature = b'\x89PNG\r\n\x1a\n'
if f.read(len(PngSignature)) != PngSignature:
    raise Exception('Invalid PNG Signature')

chunks = pyoka.get_chunks(f)

print([chunk_type for chunk_type, chunk_data in chunks])

width, height = pyoka.IHDR_sanity_check(chunks[0][1], [0, 0, 6, 8, 0] )

IDAT_data = b''.join(chunk_data for chunk_type, chunk_data in chunks if chunk_type == b'IDAT')

IDAT_data = decompress(IDAT_data)

print(len(IDAT_data), type(IDAT_data))

recon = pyoka.get_IDATA_pixel(IDAT_data, width, height)

plt.imshow(array(recon).reshape((height, width, 4)))
plt.show()