def main(a_app, a_config):
    global app, config, api, site, client_api
    app = a_app
    config = a_config
    
    from . import api, site, client_api
