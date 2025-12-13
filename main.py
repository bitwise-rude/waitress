import socket
import logging
import pathlib
import argparse

logger = logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser()

class State:
    def __init__(self):
        self.args : argparse.Namespace | None  = None

    def manage_arguments(self)->None:
        parser.add_argument("--text",help="Serve a simple text")
        parser.add_argument("--file",help="Serve a simple file")
        self.args = parser.parse_args()
     
        
state = State()

class Client:
    def __init__(self, client_handle:socket.socket) -> None:
        self.client_handle = client_handle
    
    def process(self) -> None:
        logging.info("[PROCESSING THE CLIENT]")

        data_in_str  = self.client_handle.recv(1024).decode()
        # TODO: process the input 
        self.send_output()
    
    def send_output(self)-> None:
        if state.args.text:
            logging.info(f"[SENDING A STRING OUTPUT {state.args.text}")

            message = f"HTTP/1.1 200 OK\r\n\r\n{state.args.text}" 
            self.client_handle.send(message.encode())
        
        elif state.args.file:
            logging.info(f"[SENDING A STRING OUTPUT {state.args.text}")

            # read the file
            file_path = pathlib.Path(state.args.file)
            if file_path.exists():
                message = file_path.read_text()
            else:
                logging.error("[FILE NOT FOUND]")
                message = "FILE NOT FOUND"
            
            message = f"HTTP/1.1 200 OK\r\n\r\n{message}"
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



