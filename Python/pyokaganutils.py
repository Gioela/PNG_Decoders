import struct
import zlib

def read_chunk(f):
    # Returns (chunk_type, chunk_data)
    chunk_length, chunk_type = struct.unpack('>I4s', f.read(8))
    chunk_data = f.read(chunk_length)
    checksum = zlib.crc32(chunk_data, zlib.crc32(struct.pack('>4s', chunk_type)))
    chunk_crc, = struct.unpack('>I', f.read(4))
    if chunk_crc != checksum:
        raise Exception('chunk checksum failed {} != {}'.format(chunk_crc,
            checksum))
    return chunk_type, chunk_data

def get_chunks(f):
    result = list()
    while True:
        chunk_type, chunk_data = read_chunk(f)
        result.append( (chunk_type, chunk_data) )
        if chunk_type == b'IEND':
            break
    return result

def IHDR_sanity_check(chunck, list_sanity_check):
    width, height, bitd, colort, compm, filterm, interlacem = struct.unpack('>IIBBBBB', chunck) 
    if compm != list_sanity_check[0]:
        raise Exception('invalid compression method')
    if filterm != list_sanity_check[1]:
        raise Exception('invalid filter method')

    if colort != list_sanity_check[2]:
        raise Exception('we only support truecolor with alpha')
    if bitd != list_sanity_check[3]:
        raise Exception('we only support a bit depth of 8')
    if interlacem != list_sanity_check[4]:
        raise Exception('we only support no interlacing')
    
    print(f"width: {width} height: {height}")
    return width, height

def _paethPredictor(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        Pr = a
    elif pb <= pc:
        Pr = b
    else:
        Pr = c
    return Pr

def _recon_a(recon, stride, r, c, bytes_4_pixel):
    return recon[r * stride + c - bytes_4_pixel] if c >= bytes_4_pixel else 0

def _recon_b(recon, stride, r, c):
    return recon[(r-1) * stride + c] if r > 0 else 0

def _recon_c(recon, stride, r, c, bytes_4_pixel):
    return recon[(r-1) * stride + c - bytes_4_pixel] if r > 0 and c >= bytes_4_pixel else 0

def get_IDATA_pixel(IDAT, width, height, bytes_4_pixel = 4):
    recon = []
    stride = width * bytes_4_pixel

    i = 0
    for r in range(height): # for each scanline
        filter_type = IDAT[i] # first byte of scanline is filter type
        i += 1
        for c in range(stride): # for each byte in scanline
            Filt_x = IDAT[i]
            i += 1
            if filter_type == 0: # None
                Recon_x = Filt_x
            elif filter_type == 1: # Sub
                Recon_x = Filt_x + _recon_a(recon, stride, r, c, bytes_4_pixel)
            elif filter_type == 2: # Up
                Recon_x = Filt_x + _recon_b(recon, stride, r, c)
            elif filter_type == 3: # Average
                Recon_x = Filt_x + (_recon_a(recon, stride, r, c, bytes_4_pixel) +
                                    _recon_b(recon, stride, r, c)
                                    ) // 2
            elif filter_type == 4: # Paeth
                Recon_x = Filt_x + _paethPredictor( _recon_a(recon, stride, r, c, bytes_4_pixel), 
                                                    _recon_b(recon, stride, r, c), 
                                                    _recon_c(recon, stride, r, c, bytes_4_pixel) )
            else:
                raise Exception('unknown filter type: ' + str(filter_type))
            recon.append(Recon_x & 0xff) # truncation to byte
    return recon

