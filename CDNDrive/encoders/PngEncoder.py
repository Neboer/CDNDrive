import sys
import struct
import math
from PIL import Image
from io import BytesIO

class PngEncoder:

    def __init__(self):
        self.minw = 10
        self.minh = 10
        self.dep = 3
        self.mode = 'RGB'

    @staticmethod
    def bmp_header(data):
        return b"BM" \
            + struct.pack("<l", 14 + 40 + 8 + len(data)) \
            + b"\x00\x00" \
            + b"\x00\x00" \
            + b"\x3e\x00\x00\x00" \
            + b"\x28\x00\x00\x00" \
            + struct.pack("<l", len(data)) \
            + b"\x01\x00\x00\x00" \
            + b"\x01\x00" \
            + b"\x01\x00" \
            + b"\x00\x00\x00\x00" \
            + struct.pack("<l", math.ceil(len(data) / 8)) \
            + b"\x00\x00\x00\x00" \
            + b"\x00\x00\x00\x00" \
            + b"\x00\x00\x00\x00" \
            + b"\x00\x00\x00\x00" \
            + b"\x00\x00\x00\x00\xff\xff\xff\x00"

    def encode_bmp(self, data):
        return PngEncoder.bmp_header(data) + data
        
        
    def decode_bmp(self, data):
        return data[62:]
        
    
    def encode_png(self, data):
        # 在data二进制的最前面加上被python解释为unsigned int的little-endian二进制整数信息，值等于其长度
        data = struct.pack('<I', len(data)) + data
        # 宽度*高度*深度，描述一张图片
        minsz = self.minw * self.minh * self.dep
        if len(data) < minsz:
            data += b'\0' * (minsz - len(data))
        # 将data拆开，拆成深度个份，深度默认为3，side是一深度层的边长，取天花板以防容量不够。
        side = math.ceil(math.sqrt(len(data) / self.dep))
        # total是准备好的文件容器的总容量
        total = side * side * self.dep
        # 有可能data不能填满容器，这个时候就在数据的最后补0, 填满容器。
        if len(data) < total:
            data += b'\0' * (total - len(data))
        # 将framebuffer格式的图片（也就是像素）转换为png格式，这个转换不涉及到内存的拷贝，因为是“load”的行为。
        img = Image.frombytes(self.mode, (side, side), data)
        bio = BytesIO()
        img.save(bio, 'png')
        return bio.getvalue()
    
    def decode_png(self, data):
        img = Image.open(BytesIO(data))
        data = img.tobytes()
        
        sz = struct.unpack('<I', data[:4])[0]
        data = data[4:4+sz]
        return data
    
    encode = encode_png
    
    def decode(self, data):
        if data[:4] == b'\x89PNG':
            return self.decode_png(data)
        elif data[:2] == b'BM':
            return self.decode_bmp(data)
        else: raise ValueError('unknown format')
    

def main():
    op = sys.argv[1]
    if op not in ['d', 'e']: return
    fname = sys.argv[2]
    data = open(fname, 'rb').read()
    encoder = PngEncoder()
    if op == 'e':
        data = encoder.encode(data)
        fname = fname + '.png'
    else:
        data = encoder.decode(data)
        fname = fname + '.data'
    
    with open(sys.argv[3], 'wb') as f:
        f.write(data)
        
if __name__ == '__main__': main()