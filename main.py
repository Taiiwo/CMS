from taiicms import app, socket, config


def main():
    socket.run(app, config["bind_addr"], config["port"], debug=config["debug"])

if __name__ == "__main__":
    main()
