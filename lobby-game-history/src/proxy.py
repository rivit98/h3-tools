import argparse
import threading

from pwn import remote,listen

from config import config
from proxy.handlers import send_th, recv_th


# from packets import msg_types, fake_login


#  API <-------- coro <-------- game
#  API ------->  coro --------> game



def run_proxy(game_sock, api_sock):
    forwarder = threading.Thread(target=send_th, args=(game_sock, api_sock))
    receiver = threading.Thread(target=recv_th, args=(api_sock, game_sock))
    forwarder.start()
    receiver.start()
    forwarder.join()
    receiver.join()


def proxy(target):
    with listen(port=config.lobby.port, bindaddr=target) as listener:
        with remote(config.lobby.host, config.lobby.port) as api_sock:
            game_sock = listener.wait_for_connection()
            run_proxy(game_sock, api_sock)


def standalone():
    with remote(config.lobby.host, config.lobby.port) as api_sock:
        run_proxy(None, api_sock)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--standalone", action='store_true', default=False)
    parser.add_argument("--local-ip", type=str, required=False)

    args = parser.parse_args()
    if args.standalone:
        standalone()
    else:
        if not args.local_ip:
            parser.error("--local-ip is required when using proxy mode")
            exit(1)

        proxy(args.local_ip)
