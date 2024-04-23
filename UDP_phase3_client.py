# UDP Phase #3 Client Process
# By Andrew Woods, Omar Said, and Max Borek

from socket import*     # Include Python's socket library
from PIL import Image   # Pillow Library used for importing image
import io               # Allows image to be converted to array of bytes
import time             # Needed to track run times


# CheckSum function to check for Bit errors in packet
def check_sum(packet):
    cs = 0   # Initialize CS to store result

    # Iterate over packet, depending on its length and checking 2 bytes at a time
    for i in range(0, len(packet), 2):
        # Check if two bytes are available for XOR with check_sum
        if i+1 < len(packet):
            word = (packet[i] << 8) + packet[i+1]   # Create 16-bit word integer from shifting first byte left by 8 bits and combining it with the next byte
        else:
            word = packet[i]    # If only one byte remaining, convert single byte into 16-bit word (unused bits remain 0)

        # XOR the created word with the check_sum value
        cs ^= word

    # return the 16-bit integer check_sum value
    return cs


# Function to send image using UDP Socket
def send_image(image_path, server_address, corruption_percent):
    # Track start time to return and find run time of sending
    start_time = time.perf_counter()
    print(f"Client Starts Time = {start_time}")

    image = Image.open(image_path)   # Open Image
    image_byte_array = io.BytesIO()  # Creates Byte array buffer for image
    image.save(image_byte_array, format=image.format)   # Saves byte array into buffer
    image_bytes = image_byte_array.getvalue()   # Retrieves byte array from buffer

    sock = socket(AF_INET, SOCK_DGRAM)  # Creates UDP socket

    payload_size = 1000     # Sets size of data payload for packets

    image_size = len(image_bytes)   # Find number of bytes in image file
    full_packets = image_size // payload_size   # Integer division to find number of full packets (1000 bytes)
    remainder_packet = image_size % payload_size    # Determines if remainder packet is necessary(packet under 1000 bytes)
    additional_packet = 1 if remainder_packet > 0 else 0    # If there is a remainder, create 1 more packet
    num_packets = full_packets + additional_packet      # Total number of packets needed for image

    # Track number of ACK errors
    ACK_errors = 0
    sn_errors = 0

    # Total number of corrupt packets and var to track amount corrupted sent
    total_corrupt_packets = int(num_packets * (corruption_percent / 100))
    corrupt_count = 0

    # print(f"Total Corrupt Packets = {total_corrupt_packets}")

    # Loop through all packets and send
    for i in range(num_packets):
        seq_num = i % 2             # Each packet will have either a 0 or 1 for sequence number
        next_seq_num = 1 - seq_num  # Ensures that if seq_num = 1 then nsn = 0 and if seq_num = 0 then nsn = 1

        # Determine start and end points of image data being sent in packet
        data_start = i * payload_size
        data_end = data_start + payload_size
        payload = image_bytes[data_start:data_end]

        # Convert seq_num and packet number and total packet num to bytes
        seq_num_bytes = seq_num.to_bytes(1, byteorder='big')
        packet_num_bytes = i.to_bytes(3, byteorder='big')
        num_packets_bytes = num_packets.to_bytes(3, byteorder='big')

        # Make Packet
        packet = seq_num_bytes + packet_num_bytes + num_packets_bytes + payload

        # Calculate CheckSum for packet and convert it to bytes
        cs = check_sum(packet)
        cs_bytes = cs.to_bytes(2, byteorder='big')

        # Create new packet with checksum before header
        packet = cs_bytes + packet

        # Create corrupted packet with payload of all zeros
        corrupted_packet = seq_num_bytes + packet_num_bytes + num_packets_bytes + bytes(len(payload))

        # If number of sent corrupt packets is less than total amount set
        if corrupt_count < total_corrupt_packets:
            sock.sendto(corrupted_packet, server_address)   # Send Corrupted packet
            corrupt_count += 1
        else:
            # Send Good Packet over socket
            sock.sendto(packet, server_address)

        # Loop until ACK(NSN) && ACK passes checksum is received from server
        while True:
            # Receive ACK
            ACK, address = sock.recvfrom(1024)
            cs_ACK, seq_num_ACK = ACK[:2], ACK[2:3]

            # Calculate check sum on ACK packet
            calc_cs = check_sum(ACK[2:])

            # Convert check sum received and the esn to ints
            recv_cs = int.from_bytes(cs_ACK, byteorder='big')
            esn = int.from_bytes(seq_num_ACK, byteorder='big')

            # If ACK! = NSN or ACK fails CheckSum => resend packet
            if esn != next_seq_num and recv_cs == calc_cs:
                # Resend Packet
                sock.sendto(packet, server_address)
                sn_errors += 1

            elif recv_cs != calc_cs:
                # Resend Packet and track number of ACK errors
                sock.sendto(packet, server_address)
                ACK_errors += 1
            else:
                break   # Exit loop after receiving acceptable ACK

    # Print ACK errors
    # print(f"ACK Errors = {ACK_errors} and Sequence # Errors = {sn_errors}")
    # Close Socket after sending all packets
    sock.close()


data_corruption_percent = 0     # Percent of data packets to be sent corrupted
ACK_loss_percent = 0            # Percent of ACKs to be dropped when received
input_image_path = r"C:\Users\awood\Desktop\Network_Design_UDP\UDP_Phase3\8k_phase3.png"   # raw(r) string needed due to \
send_image(input_image_path, ("localhost", 12000), data_corruption_percent)




