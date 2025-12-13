import socket
import logging

logger = logging.basicConfig(level=logging.INFO)


def main() -> None:
    server = socket.socket()
    
    # reuse the port quickly again
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    
    server.bind(("",8080))
    logging.info("[BOUND TO AVILABLE ADDERESSES AT PORT 8080]")


    server.listen()
    logging.info('[STARTED LISTENING]')

    c,_ = server.accept()
    logging.info('[ACCEPTED A CLIENT]')

    out:bytes = c.recv(1024)
    print(out.decode())

    c.close()
    server.close()

if __name__ == "__main__":
    main()



