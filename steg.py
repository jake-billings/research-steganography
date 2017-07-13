#!/usr/bin/env python

from PIL import Image
from time import time
import os, math, sys
import argparse

# Convenience access of write() and flush() so we can print "Loading...Done." and have Loading... and Done on the same
# line
write = sys.stdout.write
flush = sys.stdout.flush

# ENCODE_OFFSET_CONSTANT is set to the number of pixels to skip while encoding into pixels
ENCODE_OFFSET_CONSTANT = 1

# ENCODE_BYTES_PER_PIXEL is used for calculations of file size. If you skip pixels when encoding,
# you can't fit as much data in an image.
ENCODE_BYTES_PER_PIXEL = 1 / ENCODE_OFFSET_CONSTANT


# Encode a string of data into a PIL image using steganography
#
# When encoding a string or signal into an image, the following rules are used:
#
# The left three bits of the signal are encoded into the right three bits of the first color channel.
# The following three bits of the signal are encoded into the right three bits of the second color channel.
# The right two bits of the signal are encoded into the right two bits of the third color channel.
# The third bit from the right of the third color channel is set to 1 to indicate steganographic data is present
#
# input_public_image is the PIL image to encode into
# input_private_data is the string to encode
# debug prints additional information throughout the encoding process
def encode_steg(input_public_image, input_private_data, debug=False):
    # Query PIL for the width and height of the image
    width = input_public_image.size[0]
    height = input_public_image.size[1]

    # Load the pixel map from PIL
    pixel_map = input_public_image.load()

    # Flag the entire image as non-steg. The leftmost bit of the third image channel is used to indicate to the decoder
    # where image starts and ends.
    for x in range(0, width):
        for y in range(0, height):
            # The third bit from the right of the third color channel is set to 0 to indicate no steganographic data is
            # present
            pixel_map[x, y] = (pixel_map[x, y][0], pixel_map[x, y][1], (pixel_map[x, y][2] & 0xFB), pixel_map[x, y][3])

    # Iterate through our entire input signal scanning left to right and top to bottom through the image
    for i in range(0, len(input_private_data)):
        # Convert our linear signal into a left/right scan through the image
        x = i * ENCODE_OFFSET_CONSTANT % width
        y = math.floor(i * ENCODE_OFFSET_CONSTANT / width)

        # Access the pixel data at our location
        pixel = pixel_map[x, y]

        # Convert the point in the string to its binary value
        val = ord(input_private_data[i])

        # Encode the byte from the input signal into the pixel at our position in the output image
        #
        # The left three bits of the signal are encoded into the right three bits of the first color channel.
        # The following three bits of the signal are encoded into the right three bits of the second color channel.
        # The right two bits of the signal are encoded into the right two bits of the third color channel.
        # The third bit from the right of the third color channel is set to 1 to indicate steganographic data is present
        output_pixel = (((val & 0xE0) >> 5) + (pixel[0] & 0xF8),
                        ((val & 0x1C) >> 2) + (pixel[1] & 0xF8),
                        (val & 0x03) + (pixel[2] & 0xF8) + 0x04,
                        pixel[3])

        # Update the PIL image in memory
        pixel_map[x, y] = output_pixel

        # Print a debug message if we were told to.
        if i < 10 and debug:
            print i, x, y, input_private_data[i], output_pixel, val, (pixel[2] & 0x04) >> 2

    return input_public_image


# Decode a string of data from a PIL image using steganography
#
# When encoding a string or signal into an image, the following rules are used:
#
# The left three bits of the signal are encoded into the right three bits of the first color channel.
# The following three bits of the signal are encoded into the right three bits of the second color channel.
# The right two bits of the signal are encoded into the right two bits of the third color channel.
# The third bit from the right of the third color channel is set to 1 to indicate steganographic data is present
#
# input_image is the PIL image to extract the data from
# debug prints additional information throughout the decoding process
def decode_steg(input_image, debug=False):
    # Query PIL for the width and height of the image
    width = input_image.size[0]
    height = input_image.size[1]

    # Load the pixel map from PIL
    pixel_map = input_image.load()

    # Create an array to append our data to
    output_data_arr = []

    # Iterate through the image using a modulus to set x and y. This ensures we do not exceed the bounds of our image
    # despite the fact that we will probably break out of this loop because the encoded data probably does not exceed
    # the size of the image
    for i in range(0, width * height / ENCODE_OFFSET_CONSTANT):
        # Query PIL for the width and height of the image
        x = i * ENCODE_OFFSET_CONSTANT % width
        y = math.floor(i * ENCODE_OFFSET_CONSTANT / width)

        # Query the PIL pixel map for the pixel in question
        pixel = pixel_map[x, y]

        # Check the third bit from the right of the third color channel. If there's no steg data then break. We encode
        # in order, so once this bit is 0, that's the end of the stream.
        if (pixel[2] & 0x04) >> 2 < 1:
            break

        # Reconstruct the encoded byte by combining the lowest 3 bits of the first two channels and the lowest 2 bits of
        # the last
        val = ((pixel[0] & 0x07) << 5) + ((pixel[1] & 0x07) << 2) + (pixel[2] & 0x03)

        # Append the data to the output data array
        output_data_arr.append(chr(val))

        # Print some debugging messages
        if (i < 5 or (width * height / ENCODE_OFFSET_CONSTANT) - i <= 5) and debug:
            print i, x, y, chr(val), pixel_map[x, y], val, (pixel[2] & 0x04) >> 2

    # Combine the output data into a string
    output_data = ''.join(output_data_arr)

    return output_data


# Runs the encode_steg function with user interface messages; handles loading images from certain input/output paths
#
# input_public_path The path to load the input image into which the private data will be encoded into
# input_private_path The path to load the input data that will be encoded into the private image
# output_path The path to output to the encoded image to
def main_encode(input_public_path='input_public.png',
                input_private_path='input_private.jpg',
                output_path='output_encoded.png'):
    # Print a message indicating that we've started loading the public image
    write('Loading...')
    flush()
    start = time()

    # Load the image
    input_public_image = Image.open(input_public_path)

    # Print a message indicating that we've finished
    print 'Done in %ss.' % (time() - start)

    # Check the size of the input data and the available bytes we have to encode it
    required_bytes = os.path.getsize(input_private_path)
    available_bytes = input_public_image.size[0] * input_public_image.size[1] * ENCODE_BYTES_PER_PIXEL

    # Print the size of the input data and the available bytes we have to encode it
    print '%s bytes available for encoding in %s' % (available_bytes, input_public_path)
    print '%s bytes required for encoding of %s' % (required_bytes, input_private_path)

    # Don't try to encode data into an image if the image isn't large enough. Just show an error message.
    if required_bytes > available_bytes:
        print '%s is not large enough to hold %s.' % (input_public_path, input_private_path)
        return

    # Announce the start of encoding
    write('Encoding...')
    flush()
    start = time()

    # Read the input data, encode it, and output it
    with open(input_private_path, 'r') as rfile:
        # Read the input private data
        input_private_data = rfile.read(required_bytes)

        # Encode the private data into the input image to generate the output image
        output_image = encode_steg(input_public_image, input_private_data)

        # Save the output image
        output_image.save(output_path)

        # Print a message saying that we finished
        print 'Done in %ss.' % (time() - start)


# Runs the decode_steg function with user interface messages; handles loading images from certain input/output paths
#
# input_path The path to load the input image from which data will be decoded
# output_path The path to output to the encoded image to
def main_decode(input_path='output_encoded.png',
                output_path='output_private.jpg'):
    # Announce that decoding has started
    write('Decoding...')
    flush()
    start = time()

    # Load the input image
    input_image = Image.open(input_path)

    # Decode the steg data from the input image
    output_data = decode_steg(input_image)

    # Open the output file and write the output data then announce we did so
    with open(output_path, 'w') as wfile:
        # Write the output data
        wfile.write(output_data)

        # Print a message to announce we finished decoding
        print 'Done in %ss.' % (time() - start)


# Use the argparse library to invoke the appropriate functions if somebody is using the command line tool
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--encode', '-ed', dest="encode", action="store_true",
                        help="Encode the private input image into the public input image using steganography")
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

    print "I'm here, but I need directions. Help me help you help yourself by telling me what you want. " \
          "(Or run me with -h for help)"


# Run main if somebody's running this file
if __name__ == '__main__':
    main()
