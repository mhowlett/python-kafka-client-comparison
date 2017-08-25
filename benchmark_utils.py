import os
import sys

def make_url_messages(urls_per_msg):
    messages = []

    if urls_per_msg > 16:
        print('# expected urls_per_msg <= 16. aborting')
        exit(0)

    with open('/tmp/urls.10K.txt') as f:
        urls = f.readlines()

    for i in range(int(len(urls)/urls_per_msg) - 1):
        msg = ''
        for j in range(urls_per_msg):
            msg += urls[i*urls_per_msg + j]
        messages.append(msg)

    if sys.version_info >= (3, 0):
        messages = [bytes(url, 'utf-8') for url in messages]
    else:
        messages = [bytes(url) for url in messages]
    
    return messages


def make_test_message(message_len):
    message = bytearray()
    for i in range(message_len):
        message.extend([48 + i%10])
    message = bytes(message)

    return message
