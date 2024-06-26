from datetime import datetime,timedelta
from datetime import date
import asyncio
import config
import database

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    CallbackContext
)
from telegram.constants import ParseMode


db = database.Database()

def get_packages_menu():
    text = config.subsciption_msg
    package_keys = list(config.packages.keys())
    
    keyboard = []
    for package_key in package_keys:
        p_text = config.packages[package_key]["text"]
        keyboard.append([InlineKeyboardButton(p_text, callback_data=f"get_package_providers|{package_key}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back_balance_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return text, reply_markup

def get_package_providers_menu(key:str):
    package  = config.packages[key]
    provider_keys = list(package["providers"].keys())
    text = package["description"]
    keyboard = []
    for provider_key in provider_keys:
        title = package["providers"][provider_key]["title"]
        keyboard.append([InlineKeyboardButton(title, callback_data=f"send_invoice_package|{key, provider_key}")])
        
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back_packages_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return text, reply_markup

def get_contracts_menu():
    text = config.subsciption_msg
    contract_keys = list(config.contracts.keys())
        
    keyboard = []
    for contract_key in contract_keys:
        p_text = config.contracts[contract_key]["text"]
        keyboard.append([InlineKeyboardButton(p_text, callback_data=f"get_contract_providers|{contract_key}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back_balance_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return text, reply_markup

def get_contract_providers_menu(key:str):
    contact  = config.contracts[key]
    provider_keys = list(contact["providers"].keys())
    text = contact["description"]
    keyboard = []
    for provider_key in provider_keys:
        title = contact["providers"][provider_key]["title"]
        keyboard.append([InlineKeyboardButton(title, callback_data=f"send_invoice_contract|{key,provider_key}")])
        
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back_contracts_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return text, reply_markup

def get_balance_menu(user_id: int):
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    
    # count total usage statistics
    total_n_spent_dollars = 0
    total_n_used_tokens = 0

    n_used_tokens_dict = db.get_user_attribute(user_id, "n_used_tokens")
    n_generated_images = db.get_user_attribute(user_id, "n_generated_images")
    n_transcribed_seconds = db.get_user_attribute(user_id, "n_transcribed_seconds")

    details_text = "🏷️ Details:\n"
    for model_key in sorted(n_used_tokens_dict.keys()):
        n_input_tokens, n_output_tokens = n_used_tokens_dict[model_key]["n_input_tokens"], n_used_tokens_dict[model_key]["n_output_tokens"]
        total_n_used_tokens += n_input_tokens + n_output_tokens

        n_input_spent_dollars = config.models["info"][model_key]["price_per_1000_input_tokens"] * (n_input_tokens / 1000)
        n_output_spent_dollars = config.models["info"][model_key]["price_per_1000_output_tokens"] * (n_output_tokens / 1000)
        total_n_spent_dollars += n_input_spent_dollars + n_output_spent_dollars

        details_text += f"- {model_key}: <b>{n_input_spent_dollars + n_output_spent_dollars:.03f}$</b> / <b>{n_input_tokens + n_output_tokens} tokens</b>\n"

    # image generation
    image_generation_n_spent_dollars = config.models["info"]["dalle-2"]["price_per_1_image"] * n_generated_images
    if n_generated_images != 0:
        details_text += f"- DALL·E 2 (image generation): <b>{image_generation_n_spent_dollars:.03f}$</b> / <b>{n_generated_images} generated images</b>\n"

    total_n_spent_dollars += image_generation_n_spent_dollars

    # voice recognition
    voice_recognition_n_spent_dollars = config.models["info"]["whisper"]["price_per_1_min"] * (n_transcribed_seconds / 60)
    if n_transcribed_seconds != 0:
        details_text += f"- Whisper (voice recognition): <b>{voice_recognition_n_spent_dollars:.03f}$</b> / <b>{n_transcribed_seconds:.01f} seconds</b>\n"

    total_n_spent_dollars += voice_recognition_n_spent_dollars

    user_token = db.get_user_token(user_id)
    active_contract = db.get_user_active_contract(user_id)
    
    token_free = user_token["token_free_daily"]
    token_daily = user_token["token_daily"]
    token_pack = user_token["token_pack"]
    
    end_date = date.today()
    subcription = config.messages["subcription_none"]
    if active_contract is not None:
        subcription =  config.messages["subcription_not_none"].format(token_daily=token_daily, end_date=end_date)
        end_date = (active_contract["start"] + timedelta(days=active_contract["contract_len"])).date()
    
    text = config.messages["balace_menu"].format(token_free=token_free, subcription=subcription, token_pack=token_pack)
    keyboard =[]
    
    keyboard.append([InlineKeyboardButton("Subcriptions", callback_data=f"show_contracts_menu")])
    keyboard.append([InlineKeyboardButton("Token packages", callback_data=f"show_packages_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    return text, reply_markup

async def back_balance_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    text, reply_markup = get_balance_menu(context._user_id)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
async def back_contracts_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    text, reply_markup = get_contracts_menu()
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
async def back_packages_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    text, reply_markup = get_packages_menu()
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
async def show_contracts_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    text, reply_markup = get_contracts_menu()
    
    await query.message.edit_text(text,reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_packages_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    text, reply_markup = get_packages_menu()
    
    await query.message.edit_text(text,reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
async def show_contract_providers_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    key = query.data.split("|")[1]

    user_id = query.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    text, reply_markup = get_contract_providers_menu(key)
    
    await query.message.edit_text(text,reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
async def show_package_providers_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    key = query.data.split("|")[1]

    user_id = query.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    text, reply_markup = get_package_providers_menu(key)
    
    await query.message.edit_text(text,reply_markup=reply_markup, parse_mode=ParseMode.HTML)