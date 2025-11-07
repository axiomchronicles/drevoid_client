import base64
data = "YMT7IdQeXqLNQ1G0BlEdJcY3A3ioL0a9"
open("decoded.bin", "wb").write(base64.b64decode(data))
