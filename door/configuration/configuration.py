import configparser


def read_configuration():
    file = 'app_main.ini'
    config = configparser.ConfigParser()
    config.read(file)
    client = config['DEFAULT']['client']
    endpoint = config['DEFAULT']['endpoint']
    cert_path = config['DEFAULT']['cert']
    key_path = config['DEFAULT']['key']
    root_ca_path = config['DEFAULT']['root_ca']
    return {'client': client, 'endpoint': endpoint,
            'cert_path': cert_path, 'key_path': key_path,
            'root_ca_path': root_ca_path}
