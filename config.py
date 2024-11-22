import os
import sys
import sys

RUNTIME_ENVIRONMENT = os.getenv("TRADELINK_RUNTIME_ENVIRONMENT")
# if RUNTIME_ENVIRONMENT is None:
#     raise ValueError(f"missing env TRADELINK_RUNTIME_ENVIRONMENT")

#-----------------------------------------------------------------------------------------------------------------------
# DEFAULTS
#-----------------------------------------------------------------------------------------------------------------------

CCXT = {
    'retry_count':              3,
    'retry_delay':              2,
    'timeout_connection':       10,         # FIXME: this is not being used
    'timeout_data':             2,
    'max_rows_to_fetch':        500
}

DATABASE = {
    'db_name':                  'test',
    'password_seed':            None,
    'uri_template':             None,
    'username':                 None
}


# These datasets are only created on startup if the corresponding collections are empty
# For a complete reset you would have to empty the db first.
DATABASE['initial_data'] = {
    'Account': [
        {
            "name":         "bixsub1",
            "exchange_id":  "binance"
        },
    ],
    'WebSource': [
        {
            "source_name":      "postman",
            "password_seed":    "::POST--MAN--is -in-the-city.23o94.{PANSEA23}+++++++++",
            "ok_ips":           "^127.0.0.1$",
            "ok_routes":        ".*",
            "ok_strategies":    ".*"
        }
    ]
}

#-----------------------------------------------------------------------------------------------------------------------
# DEVELOPMENT
#-----------------------------------------------------------------------------------------------------------------------

if RUNTIME_ENVIRONMENT == "DEV":
    # subprocess.run([f"figlet '{RUNTIME_ENVIRONMENT}'"], shell=True)
    figlet_banner = fr"""
 ____  _______     __
|  _ \| ____\ \   / /
| | | |  _|  \ \ / /
| |_| | |___  \ V /  Worker
|____/|_____|  \_/   {str(os.getpid())}
                                                                             
"""
    # print(figlet_banner, file=sys.stderr)
    DATABASE['db_name']         = "tradelink_localhost"
    DATABASE['password_seed']   = "89327865.(devELOPmeNT++pansea).vertus.Klarinette.3Kochkurse.(88)=="
    DATABASE['uri_template']    = "mongodb://__USERNAME__:__PASSWORD__@localhost:27017/?authMechanism=SCRAM-SHA-256"
    DATABASE['username']        = "sanic_localhost"
