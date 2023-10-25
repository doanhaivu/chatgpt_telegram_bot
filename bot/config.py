import yaml
import re
import os
import dotenv
from pathlib import Path

config_dir = Path(__file__).parent.parent.resolve() / "config"

path_matcher = re.compile(r'\$\{([^}^{]+)\}')
def path_constructor(loader, node):
  ''' Extract the matched value, expand env variable, and replace the match '''
  value = node.value
  match = path_matcher.match(value)
  env_var = match.group()[2:-1]
  env_value = os.environ.get(env_var)
  if env_value is None:
    raise ValueError(f"Environment variable {env_var} is not set")
  return env_value + value[match.end():]

yaml.add_implicit_resolver('!path', path_matcher, None, yaml.SafeLoader)
yaml.add_constructor('!path', path_constructor, yaml.SafeLoader)

# load .env config
config_env = dotenv.dotenv_values(config_dir / "config.env")
#local
#config_env = dotenv.dotenv_values(config_dir / "local.env")

# load yaml config
#with open(config_dir / "config.yml", 'r', encoding="utf8") as f:
with open(config_dir / config_env['config_yml'], 'r', encoding="utf8") as f:
    config_yaml = yaml.safe_load(f)

# config parameters
telegram_token = config_env['TELEGRAM_BOT_TOKEN']
openai_api_key = config_env['OPENAI_API_KEY']
retrieval_plugin_bearer_token = config_env['RETRIEVAL_PLUGIN_BEARER_TOKEN']
openai_api_base = config_yaml.get("openai_api_base", None)
allowed_telegram_usernames = config_yaml["allowed_telegram_usernames"]
new_dialog_timeout = config_yaml["new_dialog_timeout"]
enable_message_streaming = config_yaml.get("enable_message_streaming", True)
return_n_generated_images = config_yaml.get("return_n_generated_images", 1)
n_chat_modes_per_page = config_yaml.get("n_chat_modes_per_page", 5)

#mongodb
mongodb_uri = f"mongodb://{config_env['MONGODB_DOMAIN']}:{config_env['MONGODB_PORT']}"

limit_question = config_yaml.get("limit_question", 100)
limit_token = config_yaml.get("limit_token", 50000)
unlimit_user = config_yaml["unlimit_users"]

# load message
with open(config_dir / config_env['messages_yml'], 'r', encoding="utf8") as f:
    messages_yaml = yaml.safe_load(f)
    
#messages
hi_msg = messages_yaml["hi_msg"]
nothing_to_retry = messages_yaml["nothing_to_retry"]
help_message = messages_yaml["help_message"]
help_group_message = messages_yaml["help_group_message"]

#elasticsearch
elasticsearch_endpoint = config_env['ELASTICSEARCH_ENDPOINT']
elasticsearch_username = config_env['ELASTICSEARCH_USERNAME']
elasticsearch_password = config_env['ELASTICSEARCH_PASSWORD']

subsciption_msg = messages_yaml["subsciption_msg"]

# chat_modes
# đổi chat_modes để đổi ngôn ngữ
with open(config_dir / config_env['chatmodes_yml'], 'r', encoding="utf8") as f:
    chat_modes = yaml.safe_load(f)

# models
with open(config_dir / config_env['models_yml'], 'r', encoding="utf8") as f:
    models = yaml.safe_load(f)
    
# payments
with open(config_dir / config_env['payments_yml'], 'r', encoding="utf8") as f:
    payment_yml = yaml.safe_load(f)
    
contracts = payment_yml["contracts"]
packages = payment_yml["packages"]
provider_tokens = payment_yml["provider_token"]
# files
help_group_chat_video_path = Path(__file__).parent.parent.resolve() / "static" / "help_group_chat.mp4"
