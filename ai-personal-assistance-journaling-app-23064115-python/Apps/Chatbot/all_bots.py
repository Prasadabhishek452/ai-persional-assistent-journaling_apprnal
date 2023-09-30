import os
import openai
from dotenv import load_dotenv
import redis
import uuid
import json
import datetime
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
redis_client = redis.StrictRedis(host="127.0.0.1", port=6379,db=0)

functions = [
                {
                    "name": "generate_task",
                    "description": "Generate a list of tasks with start dates and end dates based on the user's goal and related information in the conversation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conversation": {
                                "type": "array",
                                "description": "The conversation history for context.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "role": {
                                            "type": "string",
                                            "description": "The role of the message, either 'user' or 'system'."
                                        },
                                        "content": {
                                            "type": "string",
                                            "description": "The content of the message."
                                        }
                                    },
                                    "required": ["role", "content"]
                                }
                            }
                        },
                        "required": ["conversation"]
                    },
                    "returns": {
                        "type": "object",
                        "description": "An object containing the list of tasks and the updated conversation.",
                        "properties": {
                            "tasks": {
                                "type": "array",
                                "description": "A list of tasks represented as JSON objects with keys 'task', 'start_date', and 'end_date'.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "task": {
                                            "type": "string",
                                            "description": "The task description."
                                        },
                                        "start_date": {
                                            "type": "string",
                                            "description": "The start date of the task in the format 'YYYY-MM-DD'."
                                        },
                                        "end_date": {
                                            "type": "string",
                                            "description": "The end date of the task in the format 'YYYY-MM-DD'."
                                        }
                                    },
                                    "required": ["task", "start_date", "end_date"]
                                }
                            },
                            "conversation": {
                                "type": "array",
                                "description": "The updated conversation history including the system message.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "role": {
                                            "type": "string",
                                            "description": "The role of the message, either 'user' or 'system'."
                                        },
                                        "content": {
                                            "type": "string",
                                            "description": "The content of the message."
                                        }
                                    },
                                    "required": ["role", "content"]
                                }
                            }
                        },
                        "required": ["tasks", "conversation"]
                    }
                }
            ]


def generate_conversation_id(redis_client):
    while True:
        conversation_id = str(uuid.uuid4())
        key = f"conversation:{conversation_id}"
        if not redis_client.exists(key):
            return conversation_id

def get_conversation(conversation_id):
    key = f"conversation:{conversation_id}"
    conversation_json = redis_client.get(key)
    if conversation_json:
        conversation_data = json.loads(conversation_json)  # Convert JSON string to list
        return conversation_data
    return None

def save_conversation(conversation_id, conversation_data):
    key = f"conversation:{conversation_id}"
    conversation_json = json.dumps(conversation_data)  # Convert list to JSON string
    redis_client.set(key, conversation_json)



def generate_task(conversation):
    openai.api_key = api_key
    MODEL = "gpt-3.5-turbo"
    message={
        "role": "system", 
        "content": f"Generate a list of tasks with start dates and end dates based on the user's goal and related information in the conversation. The tasks list must be a list of JSON objects with keys 'task', 'start_date', and 'end_date'. Give dates in format supported by django, starting from {datetime.datetime.today()}. Do not use place holders."
        }

    conversation.append(message)
    json_instruction_message = {
        "role": "system",
        "content": 'Generate a list of tasks in the following JSON format:{"tasks":[{"task":"Task 1","start_date":"YYYY-MM-DD","end_date":"YYYY-MM-DD"},{"task":"Task 2","start_date":"YYYY-MM-DD","end_date": "YYYY-MM-DD"},]}'
    }
    conversation.append(json_instruction_message)
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=conversation,
        max_tokens=500,
    )
    tasks = json.loads(response['choices'][0]['message']['content'])
    return tasks,conversation

def goal_chat_bot(user_message,conversation_id=None):  
    openai.api_key = api_key
    MODEL = "gpt-3.5-turbo"

    if not conversation_id:
        conversation_id = generate_conversation_id(redis_client)
        conversation = [
            {
                "role": "system",
                "content": "You are a goal-setting assistant. Your goal is to help the user create their goal plan. Start by asking the user 'What goal you want to set?' and then follow up with related questions one at a time to gather more information.keep the questions short, once you have enough information ask user if they would like to generate tasks. Once the tasks are generated ask user if they are change enything, generate updated tasks until user finalizes the tasks."
            },
        ]
    else:
        conversation = get_conversation(conversation_id)
        message={
            "role": "user",
            "content":user_message
            }
        conversation.append(message)
        save_conversation(conversation_id, conversation)
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=conversation,
        max_tokens=500,
        functions=functions,
        function_call={"name": "generate_task"}
    )
    try:
        response_message=json.loads(response.choices[0].message["content"])
        print("i am the grabe",response_message)
        if response in response_message:
            assistant_response = {
                "role": "assistant",
                "content": json.dumps(response_message["response"]),
            }
    except:
        assistant_response = {
            "role": "assistant",
            "content": json.dumps({"responce":response.choices[0].message["content"]}),
        }
    conversation.append(assistant_response)
    save_conversation(conversation_id, conversation)
    
    if response.choices[0].message.get("function_call") and response.choices[0].message["function_call"]["name"] == "generate_task":
        tasks, conversation = generate_task(conversation)
        task_response = json.dumps(tasks)
        print("tasks------->",json.loads(task_response))
        task_message = {
            "role": "function",
            "name": "generate_task",
            "content": task_response,
        }
        conversation.append(task_message)
        save_conversation(conversation_id, conversation)  
    return json.loads(conversation[-1]["content"]), conversation_id







# ---------------------------------------------------------------- vision




vision_functions = [
    {
        "name": "generate_ai_vision_summary",
        "description": "Generate a concise overview of the user's vision based on conversation insights.",
        "parameters": {
            "type": "object",
            "properties": {
                "conversation": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    },
                    "description": "An array of messages representing the conversation."
                }
            },
            "required": ["conversation"]
        },
        "returns": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "The generated concise overview of the user's vision."
                }
            },
            "required": ["summary"],
            "description": "An object containing the generated vision summary."
        }
    },
    {
        "name": "generate_ai_vision_image",
        "description": "Generate an Ai image based on conversation and a summary extracted from it.",
        "parameters": {
            "type": "object",
            "properties": {
                "conversation": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    },
                    "description": "An array of messages representing the conversation."
                }
            },
            "required": ["conversation"]
        },
        "returns": {
            "type": "object",
            "properties": {
                "image_description": {
                    "type": "string",
                    "description": "The generated image description."
                }
            },
            "required": ["image_description"],
            "description": "An object containing the generated image description."
        }
    }
]






def generate_vision_conversation_id(redis_client):
    while True:
        conversation_id = str(uuid.uuid4())
        key = f"conversation:{conversation_id}"
        if not redis_client.exists(key):
            return conversation_id

def get_vision_conversation(conversation_id):
    key = f"conversation:{conversation_id}"
    conversation_json = redis_client.get(key)
    if conversation_json:
        conversation_data = json.loads(conversation_json)  # Convert JSON string to list
        return conversation_data
    return None

def save_vision_conversation(conversation_id, conversation_data):
    key = f"conversation:{conversation_id}"
    conversation_json = json.dumps(conversation_data)  # Convert list to JSON string
    redis_client.set(key, conversation_json)




def generate_ai_vision_summary(conversation):
    openai.api_key = api_key
    MODEL = "gpt-3.5-turbo"
    message={
        "role": "system", 
        "content": f"Create a concise overview of the user's vision using the insights gathered from our conversation. Craft the summary in the user's own perspective without utilizing any placeholders."
        }
    conversation.append(message)
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=conversation,
        max_tokens=500,
    )
    summary =response.choices[0].message["content"]
    return summary

def vision_image(prompt):
    openai.api_key = api_key
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="256x256",
    )
    return response["data"][0]["url"]

def generate_ai_vision_image(conversation):
    openai.api_key = api_key
    MODEL = "gpt-3.5-turbo"
    message={
        "role": "system", 
        "content": "Generate an art description that visually represents a summary extracted from the conversation. Search the conversation for a summary that provides insights about the user's long-term vision. Use the extracted summary to generate an image description."
        }
    conversation.append(message)
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=conversation,
        max_tokens=100,
    )
    prompt =response.choices[0].message["content"]
    return vision_image(prompt)

def save_to_db(conversation):
    pass

def format_conversation(conversation):
    openai.api_key = api_key
    MODEL = "gpt-3.5-turbo"
    message={
        "role": "system", 
        "content": ""
        }
    conversation.append(message)
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=conversation,
        max_tokens=100,
    )

def vision_chat_bot(user_message, conversation_id=None):  
    openai.api_key = api_key
    MODEL = "gpt-3.5-turbo"

    if not conversation_id:
        conversation_id = generate_vision_conversation_id(redis_client)
        conversation = [
            {
            "role": "system",
            "content": "You are a vision-setting assistant. Your goal is to help the user create a clear idea of their long-term vision. Start the conversation by greeting the user and asking, 'What vision do you want to set?' Follow up the conversation by asking relevant questions about the user's vision. Once you have enough information, ask the user if they would like to generate a summary. After generating a summary for the user's vision, ask them if they would like an AI-generated image for their vision."
            },
            # {
            # "role": "system",
            # "content": "Your response should be a single JSON object in the specified format: {'bot_response': 'your_response', 'summary': 'response_from_generate_ai_vision_summary_function', 'image_url': 'response_from_generate_ai_vision_image_function'}. Please make sure there is only one JSON object in your response and that it follows the provided structure. Do not include any additional JSON objects or text outside of this format."
            # }
        ]
        

    else:
        conversation = get_vision_conversation(conversation_id)
        message = {
            "role": "user",
            "content": user_message
        }
        conversation.append(message)
        save_vision_conversation(conversation_id, conversation)
        print("============>save_vision_conversation",save_vision_conversation)

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=conversation,
        max_tokens=500,
        functions=vision_functions,
        function_call="auto"
    )

    if response.choices[0].message.get("function_call") and response.choices[0].message["function_call"]["name"] == "generate_ai_vision_summary":
        summary=generate_ai_vision_summary(conversation)
        summary_message = {
            "role": "function",
            "name": "generate_ai_vision_summary",
            "content": summary,
        }
        conversation.append(summary_message)
        message={
            "role": "system", 
            "content": "Once a summary is crafted, present the summary to the user and inquire if they're interested in generating an AI-generated image to match their vision. Maintain the original language of the summary while doing so."
        }
        conversation.append(message)
        # message={
        #     "role": "system",
        #     "content": "Please return the response as a JSON object with the following format: {'bot_response': 'your_response', 'summary': 'response_from_generate_ai_vision_summary_function', 'image_url': 'response_from_generate_ai_vision_image_function'}. Ensure that the JSON object contains only the mentioned keys and adheres to the provided structure. Do not include any extra text outside the JSON object."
        # }
        # conversation.append(message)
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=conversation,
            max_tokens=500,
        )
        assistant_response = {
            "role": "assistant",
            "content": response.choices[0].message["content"],
        }
        conversation.append(assistant_response)
    elif response.choices[0].message.get("function_call") and response.choices[0].message["function_call"]["name"] == "generate_ai_vision_image":
        url=generate_ai_vision_image(conversation)
        url_message = {
            "role": "function",
            "name": "generate_ai_vision_image",
            "content": url,
        }
        conversation.append(url_message)
    
    else:
        assistant_response = {
            "role": "assistant",
            "content": response.choices[0].message["content"],
        }
        conversation.append(assistant_response)
    save_vision_conversation(conversation_id, conversation)
    return conversation[-1]["content"], conversation_id      
# /Users/admin/Desktop/AI-Work-Vorakon/ai-personal-assistance-journaling-app-23064115-python/Apps/Chatbot/all_bots.py


# /Users/admin/Desktop/AI-Work-Vorakon/ai-personal-assistance-journaling-app-23064115-python/Apps/Chatbot/tests.py
# ---------------------------------------------------------------- Journal






# ---------------------------------------------------------------- New Dairy code-------------------------------------------

diary_functions = [
    {
        "name": "generate_ai_diary_entry",
        "description": "Generate a diary entry based on the user's description of their day or thoughts.",
        "parameters": {
            "type": "object",
            "properties": {
                "conversation": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    },
                    "description": "An array of messages representing the conversation."
                }
            },
            "required": ["conversation"]
        },
        "returns": {
            "type": "object",
            "properties": {
                "diary_entry": {
                    "type": "string",
                    "description": "The generated diary entry based on the user's description."
                }
            },
            "required": ["diary_entry"],
            "description": "An object containing the generated diary entry."
        }
    },
    {
        "name": "generate_ai_diary_image",
        "description": "Generate an AI image based on a diary entry and a prompt.",
        "parameters": {
            "type": "object",
            "properties": {
                "diary_entry": {"type": "string", "description": "The user's diary entry."},
                "prompt": {"type": "string", "description": "Prompt for generating the AI image description."}
            },
            "required": ["diary_entry", "prompt"]
        },
        "returns": {
            "type": "object",
            "properties": {
                "image_description": {
                    "type": "string",
                    "description": "The generated image description."
                }
            },
            "required": ["image_description"],
            "description": "An object containing the generated image description."
        }
    }
]

def generate_diary_conversation_id(redis_client):
    while True:
        conversation_id = str(uuid.uuid4())
        key = f"diary_conversation:{conversation_id}"
        if not redis_client.exists(key):
            return conversation_id

def get_diary_conversation(conversation_id):
    key = f"diary_conversation:{conversation_id}"
    conversation_json = redis_client.get(key)
    if conversation_json:
        conversation_data = json.loads(conversation_json)
        return conversation_data
    return None

def save_diary_conversation(conversation_id, conversation_data):
    key = f"diary_conversation:{conversation_id}"
    conversation_json = json.dumps(conversation_data)
    redis_client.set(key, conversation_json)

def generate_ai_diary_entry(conversation):
    openai.api_key = api_key
    MODEL = "gpt-3.5-turbo"
    message = {
        "role": "system", 
        "content": "Create a diary entry summarizing your day or thoughts. Write freely and express yourself genuinely."
    }
    conversation.append(message)
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=conversation,
        max_tokens=500,
    )
    diary_entry = response.choices[0].message["content"]
    return diary_entry

def diary_image(prompt):
    openai.api_key = api_key
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="256x256",
    )
    return response["data"][0]["url"]


# -----------------------------------------------------------------------------------
def generate_ai_diary_image(conversation):
    openai.api_key = api_key
    MODEL = "gpt-3.5-turbo"
    message = {
        "role": "system",
        "content": "Generate an art description that visually represents a diary_entry extracted from the conversation. Search the conversation for a diary_entry that provides insights about the user's long-term vision. Use the extracted diary_entry to generate an image description."
    }
    conversation.append(message)
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=conversation,
        max_tokens=100,
    )
    prompt = response.choices[0].message["content"]
    return diary_image(prompt)

# -------------------------------------------------------------------------------------
def diary_chat_bot(user_message, conversation_id=None):
    openai.api_key = api_key
    MODEL = "gpt-3.5-turbo"

    if not conversation_id:
        conversation_id = generate_diary_conversation_id(redis_client)
        conversation = [
            {
                "role": "system",
                "content": "You are a diary assistant. Your goal is to help the user document their day or thoughts in their diary. Start the conversation by asking the user what they would like to write about today."
            }
        ]   
    else:
        conversation = get_diary_conversation(conversation_id)
        message = {
            "role": "user",
            "content": user_message
        }
        conversation.append(message)
        save_diary_conversation(conversation_id, conversation)

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=conversation,
        max_tokens=500,
        functions=diary_functions,
        function_call="auto"
    )

    if response.choices[0].message.get("function_call") and response.choices[0].message["function_call"]["name"] == "generate_ai_diary_entry":
        diary_entry = generate_ai_diary_entry(conversation)
        diary_entry_message = {
            "role": "function",
            "name": "generate_ai_diary_entry",
            "content": diary_entry,
        }
        conversation.append(diary_entry_message)
        message = {
            "role": "system",
            # "content": "Once you have finished writing your diary entry, you can choose to add an image that represents your thoughts. Would you like to add an image?"
            "content":"Once you have finished writing your diary entry,create a AI generated image that repersents your thoughts."
        }
        conversation.append(message)
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=conversation,
            max_tokens=500,
        )
        assistant_response = {
            "role": "assistant",
            "content": response.choices[0].message["content"],
        }
        conversation.append(assistant_response)
    elif response.choices[0].message.get("function_call") and response.choices[0].message["function_call"]["name"] == "generate_ai_diary_image":
        prompt = response.choices[0].message["content"]
        
        url=generate_ai_diary_image(conversation)
        url_message = {
            "role": "function",
            "name": "generate_ai_diary_image",
            "content": url,
        }
        conversation.append(url_message)
        message = {
            "role": "system",
            "content": "Here is an image that represents your diary entry. Would you like to add any additional details?"
        }
        conversation.append(message)
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=conversation,
            max_tokens=500,
        )
        assistant_response = {
            "role": "assistant",
            "content": response.choices[0].message["content"],
        }
        conversation.append(assistant_response)
    else:
        assistant_response = {
            "role": "assistant",
            "content": response.choices[0].message["content"],
        }
        conversation.append(assistant_response)
    save_diary_conversation(conversation_id, conversation)
    return conversation[-1]["content"], conversation_id
# ----------------============================================---------------------------------------

# def diary_chat_bot(user_message, conversation_id=None):
#     openai.api_key = api_key
#     MODEL = "gpt-3.5-turbo"

#     if not conversation_id:
#         conversation_id = generate_diary_conversation_id(redis_client)
#         conversation = [
#             {
#                 "role": "system",
#                 "content": "You are a diary assistant. Your goal is to help the user document their day or thoughts in their diary. Start the conversation by asking the user what they would like to write about today."
#             }
#         ]
#     else:
#         conversation = get_diary_conversation(conversation_id)
#         message = {
#             "role": "user",
#             "content": user_message
#         }
#         conversation.append(message)
#         save_diary_conversation(conversation_id, conversation)

#     response = openai.ChatCompletion.create(
#         model=MODEL,
#         messages=conversation,
#         max_tokens=500,
#         functions=diary_functions,
#         function_call="auto"
#     )

#     # Handle generating summary and AI-generated image
#     if response.choices[0].message.get("function_call"):
#         function_name = response.choices[0].message["function_call"]["name"]

#         if function_name == "generate_ai_diary_entry":
#             diary_entry = generate_ai_diary_entry(conversation)
#             diary_entry_message = {
#                 "role": "function",
#                 "name": "generate_ai_diary_entry",
#                 "content": diary_entry,
#             }
#             conversation.append(diary_entry_message)
#             message = {
#                 "role": "system",
#                 "content": "Once you have finished writing your diary entry, create an AI-generated image that represents your thoughts."
#             }
#             conversation.append(message)
        
#         elif function_name == "generate_ai_diary_image":
#             prompt = response.choices[0].message["content"]
#             url = generate_ai_diary_image(conversation)
#             url_message = {
#                 "role": "function",
#                 "name": "generate_ai_diary_image",
#                 "content": url,
#             }
#             conversation.append(url_message)
#             message = {
#                 "role": "system",
#                 "content": "Here is an image that represents your diary entry. Would you like to add any additional details?"
#             }
#             conversation.append(message)

#     else:
#         assistant_response = {
#             "role": "assistant",
#             "content": response.choices[0].message["content"],
#         }
#         conversation.append(assistant_response)
    
#     # Save the conversation
#     save_diary_conversation(conversation_id, conversation)
    
#     return conversation[-1]["content"], conversation_id


# --------------==========================================----------------------------------------------

