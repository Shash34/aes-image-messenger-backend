from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2      # For password → AES key
from Crypto.Hash import SHA256              # For PBKDF2 hashing



def encrypt_message(message, password):
# Salt is just random bytes added to a password before turning it into a key, its so that each key is unique even if password is the same
    salt = get_random_bytes(16)   # generates 16 random bytes


# produce the 32 byte key
# count = 100000 is the # of iterations 
# PBKDF2 uses HMAC with a hash function internally SHA256 is most common 
    AES_key = PBKDF2(password, salt, 32, count=100000, hmac_hash_module=SHA256) 

# a nonce is a random value that ensures each encryption is unique, even if you encrypt the same message with the same key.
    nonce = get_random_bytes(12)

# Create a AES-GCM cipher object used to encrypt, basically sets up the lock for encryption but doesn't encrypt yet
    cipher = AES.new(AES_key, AES.MODE_GCM, nonce = nonce)

# Convert the message from words to bytes
    message_bytes = message.encode()

# Encrypt and generate the authentication tag
    encrypted_message, authentication_tag = cipher.encrypt_and_digest(message_bytes)


# print the encrypted message
    return encrypted_message, AES_key, nonce, authentication_tag, salt




# Decryption

def decrypt_message(encrypted_message, AES_key, nonce, authentication_tag):
# cipher object, will be used to decrypt the message
    cipher_for_decryption = AES.new(AES_key, AES.MODE_GCM, nonce = nonce)

# decrypt the message
    decrypted_message = cipher_for_decryption.decrypt(encrypted_message)

# verify the authentication tag to make sure nothing is tampered with
    cipher_for_decryption.verify(authentication_tag)

# convert the decrypted message from bytes to words
    message_in_string = decrypted_message.decode()

# print the message
    return message_in_string