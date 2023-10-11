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
# load yaml config
with open(config_dir / "config.yml", 'r') as f:
    config_yaml = yaml.safe_load(f)
    
# load message
with open(config_dir / "messages.yml", 'r') as f:
    messages_yaml = yaml.safe_load(f)

# load .env config
config_env = dotenv.dotenv_values(config_dir / "config.env")

# config parameters
telegram_token = config_yaml["telegram_token"]
openai_api_key = config_yaml["openai_api_key"]
openai_api_base = config_yaml.get("openai_api_base", None)
allowed_telegram_usernames = config_yaml["allowed_telegram_usernames"]
new_dialog_timeout = config_yaml["new_dialog_timeout"]
enable_message_streaming = config_yaml.get("enable_message_streaming", True)
return_n_generated_images = config_yaml.get("return_n_generated_images", 1)
n_chat_modes_per_page = config_yaml.get("n_chat_modes_per_page", 5)
mongodb_uri = f"mongodb://mongo:{config_env['MONGODB_PORT']}"
limit_question = config_yaml.get("limit_question", 100)
limit_token = config_yaml.get("limit_token", 50000)
unlimit_user = config_yaml["unlimit_users"]

#messages
hi_msg = messages_yaml["hi_msg"]
nothing_to_retry = messages_yaml["nothing_to_retry"]
help_message = messages_yaml["help_message"]
help_group_message = messages_yaml["help_group_message"]


# chat_modes
# đổi chat_modes để đổi ngôn ngữ
with open(config_dir / "chat_modes.yml", 'r') as f:
    chat_modes = yaml.safe_load(f)

# models
with open(config_dir / "models.yml", 'r') as f:
    models = yaml.safe_load(f)

# files
help_group_chat_video_path = Path(__file__).parent.parent.resolve() / "static" / "help_group_chat.mp4"
