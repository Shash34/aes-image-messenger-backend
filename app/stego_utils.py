from PIL import Image
from io import BytesIO


##################################################
# EMBED THE ENCRYPTED MESSAGE INTO THE IMAGE
##################################################


def embed_into_image(encrypted_message, salt, nonce, auth_tag, input_image_path, output_image_path):


# input_image can be a path or BytesIO
    if isinstance(input_image_path, BytesIO):
        image = Image.open(input_image_path)
    else:
        image = Image.open(input_image_path)


    pixel = image.load()    # get access to the pixel level, of all pixels 


# First we need to encrypt the salt, nonce, and authentication tag into the image

    # Convert salt to binary (16 bytes → 128 bits)
    binary_salt = ''.join([bin(byte)[2:].zfill(8) for byte in salt])
    
    # convert the nonce to binary    
    binary_nonce = ''.join([bin(b)[2:].zfill(8) for b in nonce])
    
    # conver the tag to binary
    binary_tag = ''.join([bin(b)[2:].zfill(8) for b in auth_tag])

# First we need to encrypt the length of the message first so that the program knows how long to read the encrypted message

    encrypted_message_length = len(encrypted_message)   # length of the encrypted_message 
    
    binary_encrypted_message_length = bin(encrypted_message_length)[2:].zfill(32) # some binary number; [2:] chops off the '0b" part; .zfill(32) makes it max 32 bits
    
    
# need to convert the message bytes into binary code  
# int.from_bytes will return a single huge binary number object so it'll be impossible getting each digit seperately
# so we need to iterate each digit one by one using a loop
# we already converted the message length bytes in binary, now we need to add the actual message into binary code

    binary_pieces = []                # Step 1: create a list

    for byte in encrypted_message:
        binary_code = bin(byte)[2:]  # make each byte the binary value and chop off the "0b" thing
        binary_code = binary_code.zfill(8)  # get up the 8 binary digits
        binary_pieces.append(binary_code)     # add to the list

    binary_string = binary_salt + binary_nonce + binary_tag + binary_encrypted_message_length + ''.join(binary_pieces)
# example output: 11010110  (this is the message length + the actual message as well (everything in binary))

    total_bits = len(binary_string)
    if total_bits > image.width * image.height:
        raise ValueError("Message too large to fit in the image")



# We basically converted the length of the message and the message itself into binary digits, now we need to change each pixel value to the binary digit (blue area)

# change the pixel values to the encrypted message binary code

    x = 0
    y = 0

    for digit in binary_string:
        
        if y >= image.height:
            raise ValueError("Message is too large to fit in this image")
        
        first_char = int(digit, 2)   # convert the binary character '0' or '1' into the integer '0' or '1'
        
        old_pixel_tuple = pixel[x,y] # example output (200, 0 , 1) (original image)
            
        blue_channel = old_pixel_tuple[-1]    # example output is 1 and internally python knows the binary code (00000001)
                
        blue_channel = blue_channel & ~1 # Clears the lsb so lsb always becomes 0 (00000000)
        
        blue_channel = blue_channel + first_char    # now the blue channel is the blue channel + the first char (say first_char was 1 now blue channel is 00000001)
        
        if image.mode == "RGB":
            new_pixel_tuple = (old_pixel_tuple[0], old_pixel_tuple[1], blue_channel) # make new tuple
        
        elif image.mode == "RGBA":
            new_pixel_tuple = (old_pixel_tuple[0], old_pixel_tuple[1], blue_channel, old_pixel_tuple[3]) # make new tuple

        pixel[x, y] = new_pixel_tuple   # replace that pixel with the new tuple
        
        # Move to the next pixel
        x += 1             # Move right
        if x == image.width:
            x = 0         # Start new row
            y += 1        # Move down one row

 # Save to BytesIO or path
    if isinstance(output_image_path, BytesIO):
        image.save(output_image_path, format="PNG")
    else:
        image.save(output_image_path)
    
    return output_image_path



##################################################
# EXTRACT THE ENCRYPTED MESSAGE FROM THE IMAGE
##################################################

def extract_from_image(input_image_path):

    # input_image can be path or BytesIO
    if isinstance(input_image_path, BytesIO):
        image = Image.open(input_image_path)
    else:
        image = Image.open(input_image_path)
    
    pixel = image.load()    # get access to the pixel level, of all pixels 
    
    
    # first start from (0,0)
    
    binary_length_string = ""
    binary_message_string = ""
    message_length = None
    binary_salt = ""
    binary_nonce = ""
    binary_tag = ""
    salt = None
    nonce = None
    auth_tag = None
    x = 0
    y = 0
    done = False
    
    # first we need to decrypt the message length 
    
    for y in range(image.height):
        for x in range(image.width):
        
            get_color_tuple = pixel[x,y]
    
            # get the color and get the blue value and store in a String
            blue = get_color_tuple[-1]
            
    # python should automatically get the bit version of it 
    
    
    # get the last bit 
       
            last_bit = blue & 1 # is this how you get the last bit
            
            # Read salt first (128 bits)
            if salt is None:
                binary_salt += str(last_bit)
                if len(binary_salt) == 128:
                    # convert to bytes
                    salt = bytes([int(binary_salt[i:i+8], 2) for i in range(0, 128, 8)])
                   
            # Read nonce (12 bytes → 96 bits)
            elif nonce is None:
                binary_nonce += str(last_bit)
                if len(binary_nonce) == 96:
                    nonce = bytes([int(binary_nonce[i:i+8], 2) for i in range(0, 96, 8)])
            # Read authentication tag (16 bytes → 128 bits)
            elif auth_tag is None:
                binary_tag += str(last_bit)
                if len(binary_tag) == 128:
                    auth_tag = bytes([int(binary_tag[i:i+8], 2) for i in range(0, 128, 8)])
                    
            # read the message bit 
            elif message_length is None:
            
            # add the last bit to this string until you get 32 bits
                binary_length_string = binary_length_string + str(last_bit)
            
                if len(binary_length_string) == 32:
                    message_length = int(binary_length_string, 2) # get the integer value of the length of message
            else:
                
                # Read the actual message now
                binary_message_string = binary_message_string + str(last_bit)
                
                if len(binary_message_string) == message_length * 8:
                    done = True
                    break                       # breaks the inner loop
                
        if done == True:
            break
        
    
    # Split the binary string into 8-bit chunks
    byte_list = [binary_message_string[i:i+8] for i in range(0, len(binary_message_string), 8)]
    # Convert each chunk to an integer, then to bytes
    encrypted_message = bytes([int(b, 2) for b in byte_list])


    return salt, nonce, auth_tag, encrypted_message
