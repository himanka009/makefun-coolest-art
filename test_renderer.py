"""Independent PNG reconstruction and streaming encoder regression tests."""
import io
import random
import struct
import unittest
import zlib

from main import write_png


def decode_png(data):
    """Check complete chunk framing/CRC and reconstruct all PNG filter types."""
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    offset = 8
    tags = []
    compressed = bytearray()
    while offset < len(data):
        length, = struct.unpack_from('>I', data, offset)
        tag = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        assert len(payload) == length
        crc, = struct.unpack_from('>I', data, offset + 8 + length)
        assert zlib.crc32(tag + payload) == crc
        tags.append(tag)
        if tag == b'IHDR':
            width, height, depth, color, comp, filt, interlace = struct.unpack('>IIBBBBB', payload)
            assert (depth, color, comp, filt, interlace) == (8, 2, 0, 0, 0)
        elif tag == b'IDAT':
            compressed.extend(payload)
        elif tag == b'IEND':
            assert length == 0
            assert offset + 12 == len(data)
        else:
            raise AssertionError(f'Unexpected chunk: {tag!r}')
        offset += length + 12
    assert tags[0] == b'IHDR' and tags[-1] == b'IEND'
    assert tags.count(b'IHDR') == tags.count(b'IEND') == 1
    assert all(tag == b'IDAT' for tag in tags[1:-1])
    decoder = zlib.decompressobj()
    raw = decoder.decompress(compressed) + decoder.flush()
    assert decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
    stride = width * 3
    assert len(raw) == height * (stride + 1)
    previous = bytearray(stride)
    pixels = bytearray()
    filters = set()
    for y in range(height):
        start = y * (stride + 1)
        kind = raw[start]
        assert 0 <= kind <= 4
        filters.add(kind)
        row = bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            a = row[i - 3] if i >= 3 else 0
            b = previous[i]
            c = previous[i - 3] if i >= 3 else 0
            if kind == 0:
                predictor = 0
            elif kind == 1:
                predictor = a
            elif kind == 2:
                predictor = b
            elif kind == 3:
                predictor = (a + b) // 2
            else:
                p = a + b - c
                distances = (abs(p - a), abs(p - b), abs(p - c))
                predictor = (a, b, c)[distances.index(min(distances))]
            row[i] = (row[i] + predictor) & 255
        pixels.extend(row)
        previous = row
    return width, height, bytes(pixels), filters


class EncoderTests(unittest.TestCase):
    def round_trip(self, rows, width):
        destination = io.BytesIO()
        write_png(destination, iter(rows), width, len(rows))
        w, h, pixels, _ = decode_png(destination.getvalue())
        self.assertEqual((w, h, pixels), (width, len(rows), b''.join(rows)))
        return destination.getvalue()

    def test_sub_prediction_and_byte_wrap(self):
        self.round_trip([bytes([255, 0, 128])], 1)
        rows = [bytes((x * 73 + y * 19) % 256 for x in range(51)) for y in range(23)]
        self.round_trip(rows, 17)
        _, _, _, filters = decode_png(self.round_trip([bytes(range(60))] * 5, 20))
        self.assertEqual(filters, {1})

    def test_multiple_idat_chunks(self):
        rng = random.Random(91)
        data = self.round_trip([rng.randbytes(1024 * 3) for _ in range(40)], 1024)
        self.assertGreater(data.count(b'IDAT'), 1)

    def test_reused_mutable_row(self):
        def rows():
            row = bytearray(9)
            for y in range(12):
                row[:] = bytes([y * 23 % 256]) * 9
                yield row
        out = io.BytesIO()
        write_png(out, rows(), 3, 12)
        self.assertEqual(decode_png(out.getvalue())[2], b''.join(bytes(r) for r in rows()))

    def test_invalid_sources(self):
        for rows, width, height in (([], 0, 1), ([], 1, 1025), ([], 1, 1),
                                    ([b'xx'], 1, 1), ([b'abc'] * 2, 1, 1)):
            with self.subTest(width=width, height=height, rows=rows):
                with self.assertRaises(ValueError):
                    write_png(io.BytesIO(), rows, width, height)


if __name__ == '__main__':
    unittest.main()
