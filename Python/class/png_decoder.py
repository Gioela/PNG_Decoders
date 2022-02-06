import matplotlib.pyplot as plt
import struct
import zlib

from numpy import array

class PNGDecoder:

    def __init__(self, input_args:list = None) -> None:
        # self.file_path = input_args[0]
        self.file_path = None
        if input_args == None or len(input_args[:5]) < 5:
            self.IHDR_parameters = [ int(x) for x in '00680']
        else:
            # self.IHDR_parameters = [ int(x) for x in input_args[1:6] ]
            self.IHDR_parameters = [ int(x) for x in input_args[0:5] ]
        self.bytes_4_pixel = 4
        self._setup()
    
    def _setup(self):
        self.png = None
        self.chunks = list()
        self.recon = []
        # sanity check parameters
        self.width = 0
        self.height = 0
        self.compm = 0
        self.filterm = 0
        self.colort = 0
        self.bitd = 0
        self.interlacem = 0
        # data into the IDATA chunk
        self.IDAT_data = None

    def load_image(self, file_path):
        ''' Load the image in give path '''
        self.file_path = file_path
        self.png = open(self.file_path, 'rb')
        
        PngSignature = b'\x89PNG\r\n\x1a\n'
        if self.png.read(len(PngSignature)) != PngSignature:
            raise Exception('Invalid PNG Signature')
    
    def _read_chunk(self):
        # Returns (chunk_type, chunk_data)
        chunk_length, chunk_type = struct.unpack('>I4s', self.png.read(8))
        chunk_data = self.png.read(chunk_length)
        checksum = zlib.crc32(chunk_data, zlib.crc32(struct.pack('>4s', chunk_type)))
        chunk_crc, = struct.unpack('>I', self.png.read(4))
        if chunk_crc != checksum:
            raise Exception('chunk checksum failed {} != {}'.format(chunk_crc,
                checksum))
        return chunk_type, chunk_data

    def _get_chunks(self):
        while True:
            chunk_type, chunk_data = self._read_chunk()
            self.chunks.append( (chunk_type, chunk_data) )
            if chunk_type == b'IEND':
                break

    def _IHDR_sanity_check(self):
        chunk = self.chunks[0][1]
        self.width, self.height, self.bitd, self.colort, self.compm, self.filterm, self.interlacem = struct.unpack('>IIBBBBB', chunk) 
        if self.compm != self.IHDR_parameters[0]:
            print(f'[ERROR][invalid compression method] read: {self.compm} asked {self.IHDR_parameters[0]}')
            raise Exception('invalid compression method')
        if self.filterm != self.IHDR_parameters[1]:
            print(f'[ERROR][invalid filter method] read: {self.filterm} asked {self.IHDR_parameters[1]}')
            raise Exception('invalid filter method')
        if self.colort != self.IHDR_parameters[2]:
            print(f'[ERROR][we only support truecolor with alpha] read: {self.colort} asked {self.IHDR_parameters[2]}')
            raise Exception('we only support truecolor with alpha')
        if self.bitd != self.IHDR_parameters[3]:
            print(f'[ERROR][we only support a bit depth of 8] read: {self.bitd} asked {self.IHDR_parameters[3]}')
            raise Exception('we only support a bit depth of 8')
        if self.interlacem != self.IHDR_parameters[4]:
            print(f'[ERROR][we only support no interlacing] read: {self.interlacem} asked {self.IHDR_parameters[4]}')
            raise Exception('we only support no interlacing')
        
        print(f"PNG details - width: {self.width} height: {self.height}")


    def _recon_a(self, stride, r, c, bytes_4_pixel):
        return self.recon[r * stride + c - bytes_4_pixel] if c >= bytes_4_pixel else 0

    def _recon_b(self, stride, r, c):
        return self.recon[(r-1) * stride + c] if r > 0 else 0

    def _recon_c(self, stride, r, c, bytes_4_pixel):
        return self.recon[(r-1) * stride + c - bytes_4_pixel] if r > 0 and c >= bytes_4_pixel else 0

    @staticmethod
    def _paethPredictor(a, b, c):
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            return a
        elif pb <= pc:
            return b
        else:
            return c
        # return pr
    
    def _get_IDATA_pixel(self):
        stride = self.width * self.bytes_4_pixel

        i = 0
        for r in range(self.height): # for each scanline
            filter_type = self.IDAT_data[i] # first byte of scanline is filter type
            i += 1
            for c in range(stride): # for each byte in scanline
                Filt_x = self.IDAT_data[i]
                i += 1
                if filter_type == 0: # None
                    Recon_x = Filt_x
                elif filter_type == 1: # Sub
                    Recon_x = Filt_x + self._recon_a(stride, r, c, self.bytes_4_pixel)
                elif filter_type == 2: # Up
                    Recon_x = Filt_x + self._recon_b(stride, r, c)
                elif filter_type == 3: # Average
                    Recon_x = Filt_x + (self._recon_a(stride, r, c, self.bytes_4_pixel) +
                                        self._recon_b(stride, r, c)
                                        ) // 2
                elif filter_type == 4: # Paeth
                    Recon_x = Filt_x + self._paethPredictor( self._recon_a(stride, r, c, self.bytes_4_pixel), 
                                                             self._recon_b(stride, r, c), 
                                                             self._recon_c(stride, r, c, self.bytes_4_pixel) )
                else:
                    raise Exception('unknown filter type: ' + str(filter_type))
                self.recon.append(Recon_x & 0xff) # truncation to byte

    def _IDAT_decompress(self):
        IDAT_temp = b''.join(chunk_data for chunk_type, chunk_data in self.chunks if chunk_type == b'IDAT')
        self.IDAT_data = zlib.decompress(IDAT_temp)
    
    def _png_printer(self):
        plt.imshow(array(self.recon).reshape((self.height, self.width, 4)))
        plt.show()

    def run(self):
        ''' Call methods to elaborate and show the png.
        NOTE: it must be called AFTER the load_image method.
        '''
        self._get_chunks()
        self._IHDR_sanity_check()
        self._IDAT_decompress()
        self._get_IDATA_pixel()
        self._png_printer()

if __name__ == '__main__':
    from sys import argv
    png_interpreter = PNGDecoder()
    png_interpreter.load_image(argv[1])
    png_interpreter.run()