import socket
import logging
import pathlib
import argparse
import threading
from dataclasses import dataclass
import cv2

logger = logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser()

#====================
MIME_MAPPINGS = {
    ".html" : "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".json": "application/json",
    ".wav" : "audio/wav",
    ".mp4" : "video/mp4"
    ""
}
#====================



    
class State:
    def __init__(self):
        self.dict_arguments: dict[str,str] = None

    def manage_arguments(self)->None:
        parser.add_argument("--text",help="Serve a simple text")
        parser.add_argument("--file",help="Serve a simple file")
        parser.add_argument("--camera",help="Stream Your camera at a certain index")
        parser.add_argument("--redirect",help="Redirect to a site")
        parser.add_argument("--download",action="store_true",help="Redirect to a site")
        parser.add_argument("--stream",action="store_true",help="Stream to the browser")

        self.dict_arguments = vars(parser.parse_args())

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
        self.keep_alive = False
    


    
    def process(self) -> None:
        logging.info("[PROCESSING THE CLIENT]")

        try:
            data_in_str  = self.client_handle.recv(1024).decode()
        except ConnectionResetError:
            logging.error("[CONNECTION ABORTED]")
            self.destroy()
            return
        print(data_in_str)
        
        if "Connection: keep-alive" in data_in_str: self.keep_alive = True 
        else: self.keep_alive = False
        
    
        self.send_output()
        self.destroy()
    
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
                sr = ServiceResponse(200,f"Content-Type: {corresponding_mime_type}",len(message),message)

                # if wanna download
                if state.dict_arguments.get("download"):
                    sr.header_type = 'Content-Type: application/octet-stream\r\nContent-Disposition: attachment; filename='+f'"{file_path.name}"'
    
                if state.dict_arguments.get("stream"):
                    sr.header_type += "\r\nTransfer-Encoding: chunked"
                    sr.len = 0 # 0 means its chunked

                return sr
        
            else:
                logging.error("[UNKNOWN FILE FORMAT DETECTED]")
                message = "UNKNOWN FILE"
        else:
            logging.error("[FILE NOT FOUND]")
            message = "FILE NOT FOUND"
        

        
        return self._string_output(message)
    

    def send_output(self)-> None:
        

        eval_hash = {
            "text": self._string_output,
            "file": self._file_output,
            "redirect": self._redirect_output,
        }

        if state.dict_arguments:
            messages: list[ServiceResponse] = [] # at the end will have all the bytes as member

            for k,v in state.dict_arguments.items():
                if v == None:
                    continue
                service = eval_hash.get(k)
                if service:
                    messages.append(service(v))
                    break

                elif k == "camera":
                
                    self.process_video(int(v))
                    self.destroy()
                    return
               
            # now send

            if messages:
                _code_response = f"HTTP/1.1 {messages[0].code} OK"
                _header_resposne = messages[0].header_type
                _body_response = messages[0].body

                if messages[0].len != 0:
                    _length_response = f"Content-Length: {messages[0].len}"

                    message = self._combine_response_lines(_code_response,
                                                        _header_resposne,
                                                            _length_response,
                                                            "",  # since HTTP expects a empty line before body
                                                            "") # for body in bytes
                    encoded_message = message.encode() + _body_response
                    self.client_handle.send(encoded_message)
                    print("[SENT MESSAGES]")
                else:
                    message = self._combine_response_lines(_code_response,
                                                           _header_resposne,
                                                           "",
                                                           "")
                    encoded_message = message.encode()
                    self.client_handle.send(encoded_message)
                    logging.info("[STREAMING BEGINS]")

                    _chunk = 20480000
                    _sent = 0

                    while _sent < len(_body_response):
                        _size = _chunk if _sent + _chunk < len(_body_response) else len(_body_response) - _sent
                        to_send = hex(_size)[2:].encode() + b"\r\n"

                        to_send += _body_response[_sent:_sent + _size]
                        _sent += _size

                        to_send += b"\r\n"

                        try:
                            self.client_handle.send(to_send)
                        except BrokenPipeError:
                            logging.error('[CONNECTION IS BROKEN, MAYBE BROWSER WILL REQUEST AGAIN]]')
                            self.destroy()
                            self.pending_package = to_send
                            return
                        except  ConnectionResetError:
                            logging.error('[CONNECTION IS BROKEN, MAYBE BROWSER WILL REQUEST AGAIN]]')
                            self.destroy()
                            self.pending_package = to_send
                            return
                    self.client_handle.send(b'0\r\n\r\n')
                    logging.info("[SENT SUCCESFULLY]")

        if self.keep_alive:
            logging.info("[STAYING ALIVE SINCE CLIENT ASKED US TO]")
            self.process()
                    
    
    def destroy(self) -> None:
        logging.info("[DESTROYED A CLIENT]")
        
        self.client_handle.close()
        

client_list:Client = []

def main() -> None:
    state.manage_arguments()

    server = socket.socket()
    
    # reuse the port quickly again
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    
    server.bind(("",8080))
    logging.info("[BOUND TO AVILABLE ADDERESSES AT PORT 8080]")


    server.listen()
    logging.info('[STARTED LISTENING]')


    for i in range(5):
        c,_ = server.accept()
        logging.info('[ACCEPTED A CLIENT]')
        client = Client(c)
        client_list.append(client)
        threading.Thread(target=client.process).start()
   

    server.close()

if __name__ == "__main__":
    main()



