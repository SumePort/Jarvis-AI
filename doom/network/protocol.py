from dataclasses import dataclass
import json,hmac,hashlib
@dataclass(frozen=True)
class Message:
    version:int
    kind:str
    request_id:str
    payload:dict
class Protocol:
    VERSION=1
    def encode(self,message,key):
        body=json.dumps(message.__dict__,sort_keys=True,separators=(",",":")).encode()
        return body.decode()+"."+hmac.new(key,body,hashlib.sha256).hexdigest()
    def decode(self,wire,key):
        raw,sig=wire.rsplit(".",1); body=raw.encode()
        if not hmac.compare_digest(hmac.new(key,body,hashlib.sha256).hexdigest(),sig): raise PermissionError("Invalid message signature")
        data=json.loads(raw)
        if data["version"]!=self.VERSION: raise ValueError("Unsupported protocol version")
        return Message(**data)
