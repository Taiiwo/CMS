from taiicms import app, socketio, config

if __name__ == "__main__":
    socketio.run(app, config["bind_addr"], config["port"], debug=config["debug"])
