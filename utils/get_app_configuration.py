import yaml
import os
from models.config.app_configuration import AppConfiguration

def get_app_configuration( 
    path: str = 'app-config.yaml'
) -> AppConfiguration | None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Error: Configuration file located at {path} not found!")
    
    with open(path, 'r') as file:
        config = yaml.safe_load(file)
        app_config = AppConfiguration.model_validate(config)

        return app_config

    return None

    


    