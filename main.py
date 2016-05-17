from taiicms import app, socket, config

if __name__ == "__main__":
    socket.run(app, config["bind_addr"], config["port"], debug=config["debug"])
