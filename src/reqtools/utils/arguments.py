from ..config import CONFIG_DEFAULT_DIR


def add_config(parser):
    parser.add_argument("-c", "--config", help=f"Directory for configuration files, default is '{CONFIG_DEFAULT_DIR}'", default=CONFIG_DEFAULT_DIR)


def add_common(parser):
    parser.add_argument("--directory", help="Input directory for processing", required=False)
    add_config(parser=parser)