from taiicms import app, socketio, config

def main():
    socketio.run(app, config["bind_addr"], config["port"], debug=config["debug"])

if __name__ == "__main__":
    main()
