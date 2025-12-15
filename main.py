import socket
import logging
import pathlib
import argparse
from dataclasses import dataclass

logger = logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser()

class State:
    def __init__(self):
        self.args : argparse.Namespace | None  = None

    def manage_arguments(self)->None:
        parser.add_argument("--text",help="Serve a simple text")
        parser.add_argument("--file",help="Serve a simple file")
        parser.add_argument("--redirect",help="Redirect to a site")
        parser.add_argument("--json",help="Serve a json file")
        self.args = parser.parse_args()

@dataclass
class ServiceResponse:
    _code : str
    _header_type : str
    _len : int
    _body : str
    
     
        
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
        return  ServiceResponse(200,"Content-Type: text/html; charset=UTF-8", len(arg), arg)

    def _redirect_output(self,arg:str) -> ServiceResponse:
        _header = f"Location: {arg}"
        return ServiceResponse(302,_header,0,"")
        
    def _file_output(self,arg:str) -> ServiceResponse:
        file_path = pathlib.Path(arg)

        if file_path.exists():
            _file_ext = file_path.suffix

            if _file_ext == "html":
                message = file_path.read_text()
            elif _file_ext == "jpg" or _file_ext == "jpeg":
                message = file_path.read_bytes()
            else:
                logging.error("[UNKNOWN FILE FORMAT DETECTED]")
                message = "UNKNOWN FILE"
        else:
            logging.error("[FILE NOT FOUND]")
            message = "FILE NOT FOUND"
        
        return self._string_output(message)
    
    def _json_output(self,arg:str) -> tuple[int,str,int,str]:
        file_path = pathlib.Path(arg)

        if file_path.exists():
            message = file_path.read_text()
        else:
            logging.error("[FILE NOT FOUND]")
            message = "FILE NOT FOUND"
        
        return ServiceResponse(302,"Content-Type: application/json",len(message),message)


    
    def send_output(self)-> None:
        dict_arguments: dict[str,str] = vars(state.args)

        eval_hash = {
            "text": self._string_output,
            "file": self._file_output,
            "redirect": self._redirect_output,
            "json": self._json_output
        }

        if dict_arguments:
            for k,v in dict_arguments.items():

                if v == None:
                    continue

                logging.info(f"[SENDING A {k.upper()} OUTPUT")
                service_response  = eval_hash[k](v)

            status = f"HTTP/1.1 {service_response._code} OK"
            type = f"{service_response._header_type}"
            content_size = f"Content-Length: {service_response._len}"
            body = service_response._body

            message = self._combine_response_lines(status,type,
                                                str(content_size),
                                                "",  # since HTTP expects a empty line before body
                                                body)
            print(message.encode())
            self.client_handle.send(message.encode())



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



