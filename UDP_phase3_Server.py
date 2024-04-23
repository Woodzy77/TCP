# UDP Phase #3 Server Process
# By Andrew Woods, Omar Said and Max Borek
import io
from socket import*     # Necessary import for socket programming
from PIL import Image   # Pillow Library used for importing image
import time             # Needed to track run times


# Function to make ACK Packets
def make_ACK_packet(esn):
    ACK_payload = 15
    ACK_data = esn.to_bytes(1, byteorder='big') + ACK_payload.to_bytes(1, byteorder='big')  # Sends 1111/ 15 and esn as ACK payload and header
    ACK_cs = check_sum(ACK_data)  # Calculates ACK check sum
    ACK_packet = ACK_cs.to_bytes(2, byteorder='big') + ACK_data  # Assembles ACK Packet

    return ACK_packet


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


# Function for receiving image file
def recv_image(bind_address, ACK_corruption_percent, data_loss_percent):
    # Setup UDP Socket
    sock = socket(AF_INET, SOCK_DGRAM)

    # Bind socket
    sock.bind(bind_address)

    # Create Dictionary of recv packets
    received_packets = {}

    # Track expected sequence number and corrupted packets
    esn = 0     # Initialize to zero
    corrupt_ACK_count = 0
    packet_count = 0
    # Loop to receive all packets
    while True:
        # Receive packet with buffer size of 1024
        # print(f"Waiting for Packet {packet_count}")
        packet, address = sock.recvfrom(1024)

        # Extract the sequence number, total number of packets, Checksum, and payload from packet
        cs = packet[:2]     # Header is first 9 bytes of packet, rest is image payload
        seq_num = int.from_bytes(packet[2:3], byteorder='big')
        packet_num = int.from_bytes(packet[3:6], byteorder='big')
        num_packets = int.from_bytes(packet[6:9], byteorder='big')
        payload = packet[9:]

        # Calculate and compare check sum based on header and payload of packet
        check_packet = packet[2:]
        recv_cs = int.from_bytes(cs, byteorder='big')
        calc_cs = check_sum(check_packet)

        # Total number of corrupt packets and var to track amount corrupted sent
        total_corrupt_ACKS = int(num_packets * (ACK_corruption_percent / 100))
        # print(f"Total corrupted ACK packets = {total_corrupt_ACKS} and Num Packets = {num_packets}")

        # Check for expected sequence number and checksum pass
        if calc_cs == recv_cs and seq_num == esn:
            # Store image payload in dictionary at location of packet number
            received_packets[packet_num] = payload
            packet_count += 1
            # Update expected Sequence Number
            esn = 1 - esn

            # Create ACK with updated esn
            ACK_packet = make_ACK_packet(esn)
            corrupted_ACK = bytes(len(ACK_packet))   # Corrupted ACK of zeros

            # If number of sent corrupt packets is less than total amount set
            if corrupt_ACK_count < total_corrupt_ACKS:
                sock.sendto(corrupted_ACK, address)  # Send Corrupted packet
                corrupt_ACK_count += 1
                # print(f"Corrupted ACT Counter = {corrupt_ACK_count}")
            else:
                # Send Good Packet over socket
                sock.sendto(ACK_packet, address)
        else:
            # Send ACK without updating sequence number
            ACK_packet = make_ACK_packet(esn)
            corrupted_ACK = bytes(len(ACK_packet))   # Creates zero packet with same length as ACK Packet

            # If number of sent corrupt packets is less than total amount set
            if corrupt_ACK_count < total_corrupt_ACKS:
                sock.sendto(corrupted_ACK, address)  # Send Corrupted packet
                corrupt_ACK_count += 1
                # print(f"Corrupted ACT Counter = {corrupt_ACK_count}")
            else:
                # Send Good Packet over socket
                sock.sendto(ACK_packet, address)
        # Check if all packets received and stamp end time
        if len(received_packets) == num_packets:
            # Track End time
            end_time = time.perf_counter()
            print(f"Server End time = {end_time}")
            break  # Exit loop
        # else:
            # print(f"Received packets = {len(received_packets)} and Total Packets = {num_packets}")

    # Print number of corrupted packets
    # print(f"Corrupted ACK Packets = {corrupt_ACK_count}")

    # Reassemble image in order of packets
    image_data = b''.join(received_packets[i] for i in sorted(received_packets))

    # Create a Bytes IO object of ordered image data
    image_data_io = io.BytesIO(image_data)

    # Open bytes data as an image with Pillow
    image = Image.open(image_data_io)

    # Save image and display
    image.save("received_image.png")
    image.show()

    # Close Socket
    sock.close()


ACK_corruption_percent = 0  # Percent of ACKS to be corrupted
data_loss_percent = 0       # Percent of Data packets received to be dropped
print("The server is ready to receive")
recv_image(("localhost", 12000), ACK_corruption_percent, data_loss_percent)

