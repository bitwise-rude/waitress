import socket
import logging
import pathlib
import argparse
from dataclasses import dataclass

logger = logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser()

#====================
MIME_MAPPINGS = {
    ".html" : "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".png": "image/png",
    ".jpg": "image/jpg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".json": "application/json"
}
#====================


    
class State:
    def __init__(self):
        self.args : argparse.Namespace | None  = None

    def manage_arguments(self)->None:
        parser.add_argument("--text",help="Serve a simple text")
        parser.add_argument("--file",help="Serve a simple file")
        parser.add_argument("--redirect",help="Redirect to a site")
        parser.add_argument("--download",action="store_true",help="Redirect to a site")

        self.args = parser.parse_args()

@dataclass
class ServiceResponse:
    code : str
    header_type : str
    len : int
    body : bytes
    
     
        
state = State()

class Client:
    def __init__(self, client_handle:socket.socket) -> None:
        self.client_handle = client_handle
    
    def process(self) -> None:
        logging.info("[PROCESSING THE CLIENT]")

        data_in_str  = self.client_handle.recv(1024).decode()
        # TODO: process the input 
        self.send_output()
    
    def _combine_response_lines(self,*lines):
        return "\r\n".join(lines)
    
    def _string_output(self,arg:str) -> ServiceResponse:
        return  ServiceResponse(200,f"Content-Type: text/html; charset=UTF-8", len(arg), arg.encode())

    def _redirect_output(self,arg:str) -> ServiceResponse:
        _header = f"Location: {arg}"
        return ServiceResponse(302,_header,0,b"")
        
    def _file_output(self,arg:str) -> ServiceResponse:
        # mime types
        file_path = pathlib.Path(arg)

        if file_path.exists():
            _file_ext = file_path.suffix
            corresponding_mime_type = MIME_MAPPINGS.get(_file_ext)
        
            if corresponding_mime_type:
                message = file_path.read_bytes()
                return ServiceResponse(200,f"Content-Type: {corresponding_mime_type}",len(message),message)
        
            else:
                logging.error("[UNKNOWN FILE FORMAT DETECTED]")
                message = "UNKNOWN FILE"
        else:
            logging.error("[FILE NOT FOUND]")
            message = "FILE NOT FOUND"
        
        return self._string_output(message)
    

    def send_output(self)-> None:
        dict_arguments: dict[str,str] = vars(state.args)

        eval_hash = {
            "text": self._string_output,
            "file": self._file_output,
            "redirect": self._redirect_output,
        }

        if dict_arguments:
            messages: list[ServiceResponse] = [] # at the end will have all the bytes as member

            for k,v in dict_arguments.items():
                if v == None:
                    continue
                service = eval_hash.get(k)
                if service:
                    messages.append(service(v))
                    break

                else:
                    print("NOT COOL")
                    quit()
            # now send
            if messages:

                _code_response = f"HTTP/1.1 {messages[0].code} OK"
                _length_response = f"Content-Length: {messages[0].len}"
                _body_response = messages[0].body

                message = self._combine_response_lines(_code_response,
                                                        _length_response,
                                                        "",  # since HTTP expects a empty line before body
                                                        "") # for body in bytes
                encoded_message = message.encode() + _body_response
                self.client_handle.send(encoded_message)

            # if dict_arguments.get("download"):
            #         messages[-1].header_type = 'application/octet-stream\nContent-Disposition: attachment; filename="file.bin"'






    def destroy(self) -> None:
        logging.info("[DESTROYED A CLIENT]")
        
        self.client_handle.close()
        


def main() -> None:
    state.manage_arguments()

    server = socket.socket()
    
    # reuse the port quickly again
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    
    server.bind(("",8080))
    logging.info("[BOUND TO AVILABLE ADDERESSES AT PORT 8080]")


    server.listen()
    logging.info('[STARTED LISTENING]')

    c,_ = server.accept()
    logging.info('[ACCEPTED A CLIENT]')
    
    client = Client(c)
    client.process()
    client.destroy()

    server.close()

if __name__ == "__main__":
    main()



