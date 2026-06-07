import pyclamd

cd = pyclamd.ClamdNetworkSocket(host="localhost", port=3310)

def scan_file(path: str):
    result = cd.scan_file(path)

    if result:
        raise Exception("Virus detected")