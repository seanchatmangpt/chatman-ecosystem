import json,sys
from .receipt import issue, replay

def main():
    data=json.load(sys.stdin); receipt=issue(data); replay(receipt)
    json.dump({"payload":receipt.payload,"digest":receipt.digest,"replay":True},sys.stdout,sort_keys=True,separators=(",",":")); sys.stdout.write("\n")
if __name__=="__main__": main()
