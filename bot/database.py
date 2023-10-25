from typing import Optional, Any

import pymongo
import uuid
from datetime import datetime, timedelta
from datetime import date
from dateutil.relativedelta import relativedelta

import config


class Database:
    def __init__(self):
        self.client = pymongo.MongoClient(config.mongodb_uri)
        self.db = self.client["chatgpt_telegram_bot"]

        self.user_collection = self.db["user"]
        self.dialog_collection = self.db["dialog"]
        self.user_daily_stats_collection = self.db["user_daily_stats"]
        self.user_daily_stats_collection.create_index([("user_id", 1), ("date", 1)],unique=True)
        self.system_config_collection = self.db["system_config"]
        self.charge_pending_collection = self.db["charge_pending"]
        self.charge_success_collection = self.db["charge_success"]
        self.package_pending_collection = self.db["package_pending"]
        self.package_success_collection = self.db["package_success"]
        self.user_contracts_collection = self.db["user_contracts"]
        self.user_tokens_collection = self.db["user_tokens"]
        
    def get_package_pending(
        self,
        charge_id:str
    ):
        return self.package_pending_collection.find_one({"_id":charge_id})
        
    def add_new_package_pending(
        self,
        user_id:int,
        chat_id:int,
        amount: float,
        token_received:float,
        provider: str,
        method: str
    ):
        charge_id = str(datetime.today().timestamp()) + str(user_id) + str(chat_id) + str(uuid.uuid4())
        charge_dict ={
            "_id": charge_id,
            "user_id": user_id,
            "chat_id": chat_id,
            "amount": amount,
            "token_received":token_received,
            "provider": provider,
            "method": method,
            "send_date": datetime.now(),
            "received_date": None,
            "status":0
        }
        
        self.package_pending_collection.insert_one(charge_dict)
        return charge_id
    
    def add_new_package_success(
        self,
        pending_dict:dict
    ):
        charge_dict ={
            "_id": pending_dict["_id"],
            "user_id": pending_dict["user_id"],
            "chat_id": pending_dict["chat_id"],
            "amount": pending_dict["amount"],
            "token_received": pending_dict["token_received"],
            "provider": pending_dict["provider"],
            "method": pending_dict["method"],
            "date": datetime.now()
        }
        
        self.package_success_collection.insert_one(charge_dict)
        self.user_buy_package(pending_dict["user_id"], pending_dict["token_received"])
        
    def update_package_success(self, charge_id:int):
        charge_dict = self.get_package_pending(charge_id)
        if charge_dict != None:
            self.package_pending_collection.update_one(
                {"_id": charge_id},
                {"$set": {"status": 1,
                          "received_date":datetime.now()}}
            )
            charge_dict["status"] = 1
            self.add_new_package_success(charge_dict)
        
    def new_user_token(self, user_id:int, token:int):
        find_dict = self.user_tokens_collection.find_one({"_id": user_id})
        if find_dict == None:
            token_dict = {
                "_id": user_id,
                "user_id": user_id,
                "token_free_daily":5000,
                "token_daily":0, #from contract
                "token_pack": token, #from token packages
                "last_update": datetime.now()
            }
            self.user_tokens_collection.insert_one(token_dict)
            
    def user_buy_package(self, user_id:int, token: int):
        find_dict = self.user_tokens_collection.find_one({"_id": user_id})
        if find_dict == None:
            token_dict = {
                "_id": user_id,
                "user_id": user_id,
                "token_free_daily":5000,
                "token_daily":0, #from contract
                "token_pack": token, #from token packages
                "last_update": datetime.now()
            }
            self.user_tokens_collection.insert_one(token_dict)
        else:
            new_pack = find_dict["token_pack"] + token
            self.user_tokens_collection.update_one(
                {"_id": user_id},
                {"$set": {"token_pack":new_pack,
                          "last_update": datetime.now()}
                }
            )
    
    def user_use_token(self, user_id:int, token:int):
        find_dict = self.user_tokens_collection.find_one({"_id": user_id})
        if find_dict == None:
            token_dict = {
                "_id": user_id,
                "user_id": user_id,
                "token_free_daily":5000 - token,
                "token_daily":0, #from contract
                "token_pack": 0, #from token packages
                "last_update": datetime.now()
            }
            self.user_tokens_collection.insert_one(token_dict)
        else:
            new_free = find_dict["token_free_daily"]
            new_daily = find_dict["token_daily"]
            new_pack = find_dict["token_pack"]
            
            if new_free<token:
                new_free = 0
                token = token - new_free
            if new_daily < token:
                new_daily = 0
                token = token - new_daily
            if new_pack < token:
                new_pack = 0
                token = token - new_pack
                
            self.user_tokens_collection.update_one(
                {"_id": user_id},
                {"$set": {"token_free_daily": new_free,
                          "token_daily":new_daily,
                          "token_pack":new_pack,
                          "last_update": datetime.now()}
                }
            )
            
    def add_or_update_user_contract(self, user_id:int, contract_len:int):
        find_dict = self.user_contracts_collection.find_one({"_id": user_id})
        if find_dict == None:
            contr_dict = {
                "_id": user_id,
                "user_id": user_id,
                "contract_len": contract_len,
                "start": datetime.now(),
                "last_update": datetime.now()
            }
            self.user_contracts_collection.insert_one(contr_dict)
        else:
            base_time = datetime(find_dict["start"]) + timedelta(days=find_dict["contract_len"])
            curr_time = datetime.now()
            diff = curr_time - base_time
            contr_len = find_dict["contract_len"]
            start = find_dict["start"]
            if diff.seconds > 0:
                contr_len = contract_len
                start = curr_time
            else:
                contr_len += contract_len                
            self.user_contracts_collection.update_one(
                {"_id": user_id},
                {"$set": {"contract_len": contr_len,
                          "start":start,
                          "last_update": datetime.now()}
                }
            )
        
    def get_charge_pending(
        self,
        charge_id:str
    ):
        return self.charge_pending_collection.find_one({"_id":charge_id})
    
    def check_if_invoice_available(self, charge_id: int, raise_exception: bool = False):
        if self.charge_pending_collection.count_documents({"_id": charge_id}) > 0:
            return True
        if self.package_pending_collection.count_documents({"_id": charge_id}) > 0:
            return True
        
        if raise_exception:
            raise ValueError(f"Charge {charge_id} does not exist")
        else:
            return False
    
    def add_new_charge_pending(
        self,
        user_id:int,
        chat_id:int,
        amount: float,
        provider: str,
        method: str
    ):
        charge_id = str(datetime.today().timestamp()) + str(user_id) + str(chat_id) + str(uuid.uuid4())
        charge_dict ={
            "_id": charge_id,
            "user_id": user_id,
            "chat_id": chat_id,
            "amount": amount,
            "provider": provider,
            "method": method,
            "send_date": datetime.now(),
            "received_date": None,
            "status":0
        }
        
        self.charge_pending_collection.insert_one(charge_dict)
        return charge_id
    
    def add_new_charge_success(
        self,
        pending_dict:dict
    ):
        charge_dict ={
            "_id": pending_dict["_id"],
            "user_id": pending_dict["user_id"],
            "chat_id": pending_dict["chat_id"],
            "amount": pending_dict["amount"],
            "provider": pending_dict["provider"],
            "method": pending_dict["method"],
            "date": datetime.now()
        }
        
        self.charge_success_collection.insert_one(charge_dict)
        self.add_or_update_user_contract(charge_dict["user_id"],7)
        
    def update_charge_success(self, charge_id:int):
        charge_dict = self.get_charge_pending(charge_id)
        if charge_dict != None:
            self.charge_pending_collection.update_one(
                {"_id": charge_id},
                {"$set": {"status": 1,
                          "received_date":datetime.now()}}
            )
            charge_dict["status"] = 1
            self.add_new_charge_success(charge_dict)
        else:
            pack_dict = self.get_package_pending(charge_id)
            if pack_dict != None:
                self.package_pending_collection.update_one(
                    {"_id": charge_id},
                    {"$set": {"status": 1,
                              "received_date":datetime.now()}}
                )
                pack_dict["status"] = 1
                self.add_new_package_success(pack_dict)

    def check_if_user_exists(self, user_id: int, raise_exception: bool = False):
        if self.user_collection.count_documents({"_id": user_id}) > 0:
            return True
        else:
            if raise_exception:
                raise ValueError(f"User {user_id} does not exist")
            else:
                return False
            
    def add_new_user(
        self,
        user_id: int,
        chat_id: int,
        username: str = "",
        first_name: str = "",
        last_name: str = "",
    ):
        user_dict = {
            "_id": user_id,
            "chat_id": chat_id,

            "username": username,
            "first_name": first_name,
            "last_name": last_name,

            "last_interaction": datetime.now(),
            "first_seen": datetime.now(),

            "current_dialog_id": None,
            "current_chat_mode": "assistant",
            "current_model": config.models["available_text_models"][0],

            #total used token
            "n_used_tokens": {},

            "n_generated_images": 0,
            "n_transcribed_seconds": 0.0  # voice message transcription
        }

        if not self.check_if_user_exists(user_id):
            self.user_collection.insert_one(user_dict)
            
    def check_if_user_daily_stats_exist(self, user_id:int, date:datetime, raise_exception: bool = False):
        if self.user_daily_stats_collection.count_documents({"user_id": user_id, "date": date}) > 0:
            return True
        else: 
            if raise_exception:
                raise ValueError(f"Stats {user_id} date {date} does not exist")
            else:
                return False
                    
    def add_new_user_daily_stats(
        self,
        user_id: int,
        date: date,
        total_token: int,
        total_chat: int,
    ):
        user_daily_stats_dict ={
            "user_id": user_id,
            "date": date,
            "total_token": total_token,
            "total_chat": total_chat
        }
        
        if not self.check_if_user_daily_stats_exist(user_id, date):
            self.user_daily_stats_collection.insert_one(user_daily_stats_dict)
        else:
            document = self.user_daily_stats_collection.find_one({"user_id": user_id, "date":date})
            newTotalToken = document["total_token"] + total_token
            newTotalChat = document["total_chat"] + total_chat
            self.user_daily_stats_collection.update_one(
                {"user_id": user_id, "date":date},
                {"$set": {"total_token": newTotalToken, 
                          "total_chat": newTotalChat}
                }
            )
            
    def get_user_daily_stats(
        self,
        user_id:int,
        date:date
    ):
        doc = self.user_daily_stats_collection.find_one({"user_id":user_id,"date":date})
        if doc :
            return doc
        else:
            return {"user_id":user_id,
                    "date":date,
                    "total_token": 0, 
                    "total_chat": 0
                    }
    
    def start_new_dialog(self, user_id: int):
        self.check_if_user_exists(user_id, raise_exception=True)
        chat_mode = self.get_user_attribute(user_id, "current_chat_mode")

        dialog = self.dialog_collection.find_one({"user_id":user_id, "chat_mode":chat_mode})
        if not dialog:
            dialog_id = str(uuid.uuid4())
            dialog_dict = {
                "_id": dialog_id,
                "user_id": user_id,
                "chat_mode": chat_mode,
                "start_time": datetime.now(),
                "model": self.get_user_attribute(user_id, "current_model"),
                "messages": []
            }

            # add new dialog
            self.dialog_collection.insert_one(dialog_dict)
        else:
            dialog_id = dialog["_id"]

        # update user's current dialog
        self.user_collection.update_one(
            {"_id": user_id},
            {"$set": {"current_dialog_id": dialog_id}}
        )

        return dialog_id
    
    def get_dialog_by_chat_mode(self, user_id: int, chat_mode: str):
        self.check_if_user_exists(user_id, raise_exception=True)
        
        dialog = self.dialog_collection.find_one({"user_id":user_id, "chat_mode":chat_mode})
        if not dialog:
            dialog_id = str(uuid.uuid4())
            dialog_dict = {
                "_id": dialog_id,
                "user_id": user_id,
                "chat_mode": chat_mode,
                "start_time": datetime.now(),
                "model": self.get_user_attribute(user_id, "current_model"),
                "messages": []
            }

            # add new dialog
            self.dialog_collection.insert_one(dialog_dict)
        else:
            dialog_id = dialog["_id"]
            
        # update user's current dialog
        self.user_collection.update_one(
            {"_id": user_id},
            {"$set": {"current_dialog_id": dialog_id}}
        )

        return dialog_id
            

    def get_user_attribute(self, user_id: int, key: str):
        self.check_if_user_exists(user_id, raise_exception=True)
        user_dict = self.user_collection.find_one({"_id": user_id})

        if key not in user_dict:
            return None

        return user_dict[key]

    def set_user_attribute(self, user_id: int, key: str, value: Any):
        self.check_if_user_exists(user_id, raise_exception=True)
        self.user_collection.update_one({"_id": user_id}, {"$set": {key: value}})

    def update_n_used_tokens(self, user_id: int, model: str, n_input_tokens: int, n_output_tokens: int):
        n_used_tokens_dict = self.get_user_attribute(user_id, "n_used_tokens")

        if model in n_used_tokens_dict:
            n_used_tokens_dict[model]["n_input_tokens"] += n_input_tokens
            n_used_tokens_dict[model]["n_output_tokens"] += n_output_tokens
        else:
            n_used_tokens_dict[model] = {
                "n_input_tokens": n_input_tokens,
                "n_output_tokens": n_output_tokens
            }

        self.set_user_attribute(user_id, "n_used_tokens", n_used_tokens_dict)

    def get_dialog_messages(self, user_id: int, dialog_id: Optional[str] = None):
        self.check_if_user_exists(user_id, raise_exception=True)

        if dialog_id is None:
            dialog_id = self.get_user_attribute(user_id, "current_dialog_id")

        dialog_dict = self.dialog_collection.find_one({"_id": dialog_id, "user_id": user_id})
        size = len(dialog_dict["messages"])
        if size > 10:
            size = 10
        return dialog_dict["messages"][-10:]

    def set_dialog_messages(self, user_id: int, dialog_messages: list, dialog_id: Optional[str] = None):
        self.check_if_user_exists(user_id, raise_exception=True)

        if dialog_id is None:
            dialog_id = self.get_user_attribute(user_id, "current_dialog_id")

        self.dialog_collection.update_one(
            {"_id": dialog_id, "user_id": user_id},
            {"$set": {"messages": dialog_messages}}
        )
