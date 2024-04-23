# TCP Client Process

from socket import*     # Include Python's socket library
from PIL import Image   # Pillow Library used for importing image
import io               # Allows image to be converted to array of bytes
import time             # Needed to track run times

def tcp_send(image_path, server_address):

    image = Image.open(image_path)  # Open Image
    image_byte_array = io.BytesIO()  # Creates Byte array buffer for image
    image.save(image_byte_array, format=image.format)  # Saves byte array into buffer
    image_bytes = image_byte_array.getvalue()  # Retrieves byte array from buffer



send_image_path = r"/Users/andrew/Desktop/TCP/Tokyo_4k.jpg"
tcp_send(send_image_path, ("localhost", 12000))