from channels.generic.websocket import AsyncJsonWebsocketConsumer
import asyncio
from .all_bots import *
import json
import base64


# conversation = []

# class MyAsyncJsonWebsocketConsumer(AsyncJsonWebsocketConsumer):
#     async def connect(self):
#         print("connection successfully...")
#         await self.accept()

#     async def receive(self, text_data=None, bytes_data=None, **kwargs):
#         message_type = kwargs.get('message_type')  # Get the message_type from kwargs
#         summary_generate = kwargs.get('summary_generate')  # Get the summary_generate from kwargs

#         # Validate input data (optional but recommended)
#         if text_data is not None:
#             content = await self.decode_json(text_data)
#         elif bytes_data is not None:
#             content = bytes_data
#         else:
#             # Handle invalid input gracefully (send an error response, close the connection, etc.)
#             return

#         await self.process_message(content, message_type=message_type, summary_generate=summary_generate, **kwargs)

#     async def process_message(self, content, message_type, summary_generate, **kwargs):
#         global conversation  # Use the global variable for conversation list

#         print("Message received from client..", content)

#         try:
#             if message_type == "binary":
#                 # Assuming content is base64 encoded binary data
#                 binary_data = base64.b64decode(content)
#                 user_message = binary_data.decode('utf-8')  # Convert binary to string
#             else:
#                 user_message = content.get('message', '')

#             # Define roles
#             user_role = "user"
#             bot_role = "bot"

#             print(f"{user_role}: {user_message}")

#             # Append the user's message to the conversation history
#             conversation.append({user_role: user_message})

#             # Call the chat_with_bot function here to get bot's response
#             bot_response = chat_with_bot(user_message)

#             print(f"{bot_role}: {bot_response}")

#             # Append the bot's response to the conversation history
#             conversation.append({bot_role: bot_response})

#             # summary----
#             if summary_generate == "summary_generate":
#                 # Call the generate_ai_summary function here using the entire conversation history
#                 summary = generate_ai_summary(conversation)
#                 print("=====Summary====>", summary, "<===Summary====")
#                 bot_response = summary

#             response_content = {
#                 "message_type": message_type,
#                 "goal_chatbot": bot_response
#             }

#             # If the message type is binary, encode the response back to base64
#             if message_type == "binary":
#                 response_content["goal_chatbot"] = base64.b64encode(bot_response.encode('utf-8')).decode('utf-8')

#             await self.send_json(response_content)

#         except json.JSONDecodeError:
#             await self.send_json({"message": "Invalid JSON format. Please send a valid JSON object."})

#     async def disconnect(self, code):
#         print("websocket disconnected..", code)








class MyAsyncJsonWebsocketConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("connection successfully...")
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        message_type = kwargs.get('message_type')  
        summary_generate = kwargs.get('summary_generate')  

        if text_data is not None:
            content = await self.decode_json(text_data)
        elif bytes_data is not None:
            content = bytes_data
        else:
            return

        await self.process_message(content, message_type=message_type, summary_generate=summary_generate, **kwargs)

    async def process_message(self, content, message_type, summary_generate, **kwargs):
        global conversation  # Use the global variable for conversation list

        print("Message received from client..", content)
        user_message = content.get('user_message', '')
        conversation_id = content.get('conversation_id', None)
        print("user_message", user_message)
        bot_response,conversation_id=goal_chat_bot(user_message,conversation_id)
        response_content = {
                "chatbot": bot_response,
                "conversation_id":conversation_id
            }
        await self.send_json(response_content)

    async def disconnect(self, code):
        print("websocket disconnected..", code)




class AsyncSocketVision(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("connection successfully...")
        await self.accept()
        
    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        message_type = kwargs.get('message_type')  
        summary_generate = kwargs.get('summary_generate') 
        
        
        if text_data is not None:
            content = await self.decode_json(text_data)
        elif bytes_data is not None:
            content = bytes_data
        else:
            return
        
        
        await self.process_message(content, message_type=message_type, summary_generate=summary_generate, **kwargs)
    
    async def process_message(self, content, message_type, summary_generate, **kwargs):
        global conversation  # Use the global variable for conversation list
        
        
        print("Message received from client..", content)
        user_message = content.get('user_message', '')
        conversation_id = content.get('conversation_id', None)
        print("user_message", user_message)
        bot_response,conversation_id=vision_chat_bot(user_message,conversation_id)
       
        response_content = {
                "chatbot": bot_response,
                "conversation_id":conversation_id
            }
        await self.send_json(response_content)

    async def disconnect(self, code):
        print("websocket disconnected..", code)



# -----------------------------------------------------Diary------------------------------------------------------------


# class AsyncSocketDairy(AsyncJsonWebsocketConsumer):
#     async def connect(self):
#         print("connection successfully...")
#         await self.accept()
        
#     async def receive(self, text_data=None, bytes_data=None, **kwargs):
#         message_type = kwargs.get('message_type')  
#         summary_generate = kwargs.get('summary_generate') 
        
        
#         if text_data is not None:
#             content = await self.decode_json(text_data)
#         elif bytes_data is not None:
#             content = bytes_data
#         else:
#             return
        
        
#         await self.process_message(content, message_type=message_type, summary_generate=summary_generate, **kwargs)
    
#     async def process_message(self, content, message_type, summary_generate, **kwargs):
#         global conversation  
        
        
#         print("Message received from client..", content)
#         user_message = content.get('user_message', '')
#         conversation_id = content.get('conversation_id', None)
#         print("user_message", user_message)
        
#         bot_response,conversation_id=diary_chat_bot(user_message,conversation_id)
#         response_content = {
#                 "chatbot": bot_response,
#                 "conversation_id":conversation_id
#             }
#         await self.send_json(response_content)

#     async def disconnect(self, code):
#         print("websocket disconnected..", code)



import json
import uuid
import redis
import openai
import speech_recognition as sr
from gtts import gTTS
import tempfile
from channels.generic.websocket import AsyncJsonWebsocketConsumer
class AsyncSocketDairy(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("connection successfully...")
        await self.accept()
        
    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        message_type = kwargs.get('message_type')
        summary_generate = kwargs.get('summary_generate')

        if text_data is not None:
            content = await self.decode_json(text_data)
        elif bytes_data is not None:
            content = bytes_data
        else:
            return

        await self.process_message(content, message_type=message_type, summary_generate=summary_generate, **kwargs)

    async def process_message(self, content, message_type, summary_generate, **kwargs):
        global conversation

        user_message = content.get('user_message', '')
        is_voice_message = content.get('is_voice_message', False)  
        conversation_id = content.get('conversation_id', None)

        if is_voice_message:
            user_message = self.convert_voice_to_text(user_message)

        bot_response, conversation_id = diary_chat_bot(user_message, conversation_id)

        if is_voice_message:
            bot_response = self.convert_text_to_voice(bot_response)

        response_content = {
            "chatbot": bot_response,
            "conversation_id": conversation_id
        }
        await self.send_json(response_content)

    def convert_voice_to_text(self, voice_data):
        recognizer = sr.Recognizer()
        with sr.AudioFile(voice_data) as source:
            audio = recognizer.record(source)
        try:
            user_message = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            user_message = "Sorry, I couldn't understand your voice message."
        return user_message

    def convert_text_to_voice(self, text):
        tts = gTTS(text=text, lang='en')
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        tts.save(temp_file.name + ".mp3")
        return temp_file.name + ".mp3"

    async def disconnect(self, code):
        print("websocket disconnected..", code)