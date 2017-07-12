#!/usr/bin/env python

from PIL import Image
import os
import math
import argparse
import sys
from time import time

write = sys.stdout.write
flush = sys.stdout.flush

ENCODE_OFFSET_CONSTANT = 1
ENCODE_BYTES_PER_PIXEL = 1 / ENCODE_OFFSET_CONSTANT
ALPHA = 255


def encode_steg(input_public_image, input_private_data, debug=False):
    width = input_public_image.size[0]
    height = input_public_image.size[1]

    pixel_map = input_public_image.load()

    for x in range(0, width):
        for y in range(0, height):
            pixel_map[x, y] = (pixel_map[x, y][0], pixel_map[x, y][1], (pixel_map[x, y][2] & 0xFB), ALPHA)

    for i in range(0, len(input_private_data)):
        x = i * ENCODE_OFFSET_CONSTANT % width
        y = math.floor(i * ENCODE_OFFSET_CONSTANT / width)

        pixel = pixel_map[x, y]

        val = ord(input_private_data[i])
        # input_private_data_pixel = (val & 0xE0 >> 5, val & 0x18 >> 3, val & 0x07)
        # input_public_data_pixel_masked = (pixel[0] & 0xF8, pixel[1] & 0xFC, pixel[2] & 0xF8)

        output_pixel = (((val & 0xE0) >> 5) + (pixel[0] & 0xF8),
                        ((val & 0x1C) >> 2) + (pixel[1] & 0xF8),
                        (val & 0x03) + (pixel[2] & 0xF8) + 0x04,
                        ALPHA)

        pixel_map[x, y] = output_pixel

        if i < 10 and debug:
            print i, x, y, input_private_data[i], output_pixel, val, (pixel[2] & 0x04) >> 2

    return input_public_image


def decode_steg(input_image, debug=False):
    width = input_image.size[0]
    height = input_image.size[1]

    pixel_map = input_image.load()

    output_data_arr = []

    for i in range(0, width * height / ENCODE_OFFSET_CONSTANT):
        x = i * ENCODE_OFFSET_CONSTANT % width
        y = math.floor(i * ENCODE_OFFSET_CONSTANT / width)
        pixel = pixel_map[x, y]

        if (pixel[2] & 0x04) >> 2 < 1:
            break

        val = ((pixel[0] & 0x07) << 5) + ((pixel[1] & 0x07) << 2) + (pixel[2] & 0x03)

        output_data_arr.append(chr(val))

        if (i < 5 or (width * height / ENCODE_OFFSET_CONSTANT) - i <= 5) and debug:
            print i, x, y, chr(val), pixel_map[x, y], val, (pixel[2] & 0x04) >> 2

    output_data = ''.join(output_data_arr)

    return output_data


def main_encode(input_public_path='input_public.png',
                input_private_path='input_private.jpg',
                output_path='output_encoded.png'):
    write('Loading...')
    flush()
    start = time()

    input_public_image = Image.open(input_public_path)

    print 'Done in %ss.' % (time() - start)

    required_bytes = os.path.getsize(input_private_path)
    available_bytes = input_public_image.size[0] * input_public_image.size[1] * ENCODE_BYTES_PER_PIXEL

    print '%s bytes available for encoding in %s' % (available_bytes, input_public_path)
    print '%s bytes required for encoding of %s' % (required_bytes, input_private_path)

    if required_bytes > available_bytes:
        print '%s is not large enough to hold %s.' % (input_public_path, input_private_path)
        return

    write('Encoding...')
    flush()
    start = time()

    with open(input_private_path, 'r') as rfile:
        input_private_data = rfile.read(required_bytes)

        output_image = encode_steg(input_public_image, input_private_data)

        output_image.save(output_path)
        print 'Done in %ss.' % (time() - start)


def main_decode(input_path='output_encoded.png',
                output_path='output_private.jpg'):
    write('Decoding...')
    flush()
    start = time()

    input_image = Image.open(input_path)

    output_data = decode_steg(input_image)

    with open(output_path, 'w') as wfile:
        wfile.write(output_data)
        print 'Done in %ss.' % (time() - start)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--encode', '-ed', dest="encode", action="store_true",
                        help="Encode the private input image into the public input image using stegenography")
    parser.add_argument('--decode', '-dd', dest="decode", action="store_true",
                        help="Decode a private input image from a stegenographically encoded image")

    parser.add_argument('--input-private', '-ipri', dest="input_private_path", type=str,
                        help="Path to the private image for --encode")
    parser.add_argument('--input-public', '-ipub', dest="input_public_path", type=str,
                        help="Path to the public image for --encode")
    parser.add_argument('--input', '-in', dest="input_path", type=str,
                        help="Path to image for --decode")

    parser.add_argument('--output', '-out', dest='output_path', type=str,
                        help="Output file")

    args = parser.parse_args()

    if args.encode and args.decode:
        print "Can't encode and decode in the same run. Pick one."
        return

    if args.encode:
        main_encode(input_public_path=args.input_public_path,
                    input_private_path=args.input_private_path,
                    output_path=args.output_path)
        return

    if args.decode:
        main_decode(input_path=args.input_path,
                    output_path=args.output_path)
        return

    print "I'm here, but I need directions. Help me help you help yourself by telling me what you want. (Or run me with -h for help)"


if __name__ == '__main__':
    main()
