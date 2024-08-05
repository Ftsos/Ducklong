from datetime import date
import json
import os
import io
import sys
import requests
from api.runpod_whisperx_serverless_clientside.asyncio_runpod_client_helper import RunpodApiClient
#import runpod
import base64
import asyncio
import aiohttp
import google.generativeai as genai
from flask import Flask, request, jsonify;
from pydantic import BaseModel
from types import SimpleNamespace
from openai import OpenAI
from flask_cors import CORS
from dotenv import load_dotenv
from logging.config import dictConfig
#from runpod import AsyncioEndpoint, AsyncioJob


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()



OPENAI_API_KEY = os.getenv('OPEN_AI_KEY')
AWANLLM_API_KEY_ENV = os.getenv('AWANLLM_API_KEY')
CELERY_BROKER_URL = os.getenv('REDIS_CELERY_KEY')
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
RUNPOD_API_KEY = os.getenv('RUNPOD_API_FASTER_WHISPER_KEY')

safety_settings = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

client = OpenAI(api_key=OPENAI_API_KEY)
AWANLLM_API_KEY = AWANLLM_API_KEY_ENV
genai.configure(api_key=GOOGLE_API_KEY)
#runpod.api_key = RUNPOD_API_KEY

conversation_history = []
geminiChatModel = genai.GenerativeModel('gemini-pro', safety_settings=safety_settings)
chat = {}
tasks = {}
script_transcript =  SimpleNamespace(script='', transcription='')

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console"]},
    }
)

app = Flask(__name__)
CORS(app)
whisper_model_size = "large-v3"
app.config['CELERY_BROKER_URL'] = CELERY_BROKER_URL 
app.config['CELERY_RESULT_BACKEND'] = CELERY_BROKER_URL
#celery = Celery(app.name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])
#asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
client = RunpodApiClient(RUNPOD_API_KEY, "pwz6ynrk488cme")

class QuestionFormat(BaseModel):
    query: str
    choices: list
    answer: int

#tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neo-1.3B")
#model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-neo-1.3B")

def encode_audio_base64(file_path):
    with open(file_path, "rb") as audio_file:
        encoded_string = base64.b64encode(audio_file.read()).decode("utf-8")
    return encoded_string

async def transcribe_audio_file(job_id, audio_file):


    """try:
        async with aiohttp.ClientSession() as session:
            endpoint = AsyncioEndpoint("pwz6ynrk488cme", session)
            with open(audio_file + ".health", 'w') as f:
                f.write(json.dumps(endpoint.health()))
            job: AsyncioJob = await endpoint.run({"audio_base64": audio_data})
            with open(audio_file + ".test2", 'w') as f:
                await f.write(job.status())
            while True:
                status = await job.status()
                print(f"Current job status: {status}")
                if status == "COMPLETED":
                    run_request = await job.output()
                    break
                elif status in ["FAILED"]:
                    raise Exception("Job failed or encountered an error.")
                else:
                    await asyncio.sleep(1)

        transcription_to_clean = run_request
        transcription = [segment["text"].strip() for segment in transcription_to_clean["segments"]]

        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", os.path.basename(audio_file) + "-trans.txt")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write('\n'.join(transcription))

        return os.path.basename(audio_file) + "-trans.txt"
    except Exception as e:
        print(f"Error during transcription: {e}")
        raise e"""
    async with aiohttp.ClientSession() as session:
        response = await client.wait_for_api_request_completion(job_id, session, 5)
    
    transcription_to_clean = response["output"]
    with open(audio_file + ".response", 'w') as f:
        f.write(json.dumps(response))
    transcription = [segment["text"].strip() for segment in transcription_to_clean["segments"]]

    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", os.path.basename(audio_file) + "-trans.txt")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write('\n'.join(transcription))

    return os.path.basename(audio_file) + "-trans.txt"

#hf_pipeline = pipeline('text-generation', model=model, tokenizer=tokenizer, device_map='auto')

#transcribe_audio_file("D:\\DucklongTesisSeminario\\ducklong\\api\\data\\Recording Prueba Whisper.mp3")

def send_question_prompt(transcript_class, script_class): 

    # Define the prompt
    prompt = f"Transcript Class: {transcript_class} \nScript Class: {script_class}\nGive me *10* multiple choice questions about the previously provided class.Return your answer entirely in the form of a JSON object. The JSON object should have a key named 'questions' which is an array of the questions. Each quiz question should include the choices, the answer, and a brief explanation of why each choice is correct or incorrect. Don't include anything other than the JSON. The JSON properties of each question should be 'query' (which is the question), 'choices', and 'answer'. The 'choices' key should be an array of objects that contain a key called 'choice' and 'explanation';  being 'choice' the choice name, and 'explanation' should be an explanation of why that answer is either correct, or in the case it's incorrect try to make you rethink and find the correct response. The explanations shouldn't have the incorrect or correct indication. The choices shouldn't have any ordinal value like A, B, C, D or a number like 1, 2, 3, 4. The answer should be the 0-indexed number of the correct choice. Please, give the questions, choices and explanations IN SPANISH (EVERY SINGLE BIT OF CONTENT IN THE RESPONSE THAT IS NOT EXCLUSIVE TO THE JSON OBJECT GIVEN PROPERTIES NEEDS TO BE IN SPANISH). USE THE \"JSONL\" (JSON LINES) FORMAT (JSON IN ONE LINE FORMAT). YOUR RESPONSE SHOULD ONLY CONTAIN ONE JSON OBJECT IN JSON Line FORMAT, AND ONE OBJECT ONLY; NO TEXT EXPLAINING ANYTHING."

    # Call the OpenAI API to generate questions
    #response = client.completions.create(model="gpt-3.5-turbo-1106",
    #prompt=prompt,
    #max_tokens=150,
    #n=1,  
    #stop=None,
    #temperature=0.5,
    #top_p=1.0,
    #frequency_penalty=0.0,
    #presence_penalty=0.0,
    #logprobs=None)

    jsonGenerator = genai.GenerativeModel('gemini-1.5-flash', 
                                          safety_settings=safety_settings,
                              generation_config={"response_mime_type": "application/json"})
    response = jsonGenerator.generate_content(prompt)
    return jsonify(response.text)

def array_to_string(arr):
    return '\n'.join(arr)

@app.route("/api/getFiles", methods=["GET"]) 
def getAvailableFiles():
    # Get the list of files in the folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    files = os.listdir(data_dir)

    scripts = [file for file in files if file.endswith(".txt")]
    transcripts = [file for file in files if file.endswith(".srt")]

    # Return the list of files as JSON
    return jsonify({
        "scripts": scripts,
        "transcripts": transcripts
    }), 200

@app.route("/api/getCurrentFiles", methods=["GET"])
def getCurrentFiles():
    return jsonify({"script": script_transcript.script, "transcription": script_transcript.transcription}), 200

@app.route("/api/setFile", methods=['POST'])
def set_file():
    if 'transcription' not in request.json or 'script' not in request.json:
        return jsonify({"error": "Both 'transcription' and 'script' filenames must be provided"}), 400
    # Get the filenames from the request JSON
    transcription_filename = request.json['transcription']
    script_filename = request.json['script']
    # Store the file in the script_transcript object
    script_transcript.transcription = transcription_filename
    script_transcript.script = script_filename

    return jsonify({"message": "Files received successfully"}), 200 


@app.route("/api/file", methods=['POST'])
async def get_file():

    if 'transcription' not in request.files or 'script' not in request.files:
        return jsonify({"error": "Both files must be provided"}), 400

    transcription = request.files['transcription']
    script = request.files['script']

    if transcription.filename != '':
        transcription.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", transcription.filename))

    if script.filename != '':
        script.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", script.filename))
    
    audio_base64_transformed = encode_audio_base64(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", transcription.filename))
    payload = {
                
                    "audio_base64": audio_base64_transformed
                
            }
    async with aiohttp.ClientSession() as session:
        task_id = await client.send_async_api_request(payload, session, 1000000)
    await transcribe_audio_file(task_id, os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", transcription.filename))
    return jsonify({"message": "Transcription process started", "task_id": task_id}), 202

@app.route("/api/quiz/get/<task_id>/<load_if_yes>", methods=['GET'])
async def check_transcription_status(task_id, load_if_yes):
    status = tasks.get(task_id, "unknown")
    
    if status == 'PENDING':
        return jsonify({"status": "pending"}), 202
    elif status == 'COMPLETED':
        result = tasks[task_id]
        if load_if_yes.lower() == 'yes':
            script_transcript.transcription = result
        return jsonify({"status": "complete", "result": result}), 200
    elif status == 'failed':
        return jsonify({"status": "error", "message": "Transcription task failed or revoked"}), 500
    else:
        return jsonify({"status": "error", "message": "Unknown task ID"}), 400

@app.route("/api/quiz/get/", methods=['GET'])
def get_quiz():
    if(script_transcript.transcription == ''): 
        return jsonify({"error": "Transcript is either being processed or hasn't been selected"}), 400

    if(script_transcript.script == ''): 
        return jsonify({"error": "Script is either being processed or hasn't been selected"}), 400

    transcription_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", script_transcript.transcription)
    script_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", script_transcript.script)


    try:
        with open(transcription_file_path, 'r', encoding='utf-8') as f:
            transcription = f.read()
    except FileNotFoundError:
        return jsonify({"error": "Transcription file not found"}), 404

    try:
        with open(script_file_path, 'r', encoding='utf-8') as f:
            script = f.read()
    except FileNotFoundError:
        return jsonify({"error": "Script file not found"}), 404

    return send_question_prompt(transcription, script)


@app.route("/api/quiz/answer", methods=['POST'])
def get_responses():
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), str(date.today()) + "-Quiz.json")

    # Load existing JSON content if the file exists
    try:
        with open(filename, "r") as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    # Ensure existing data is an array
    if not isinstance(existing_data, list):
        existing_data = [existing_data]

    # Append new data to the existing array
    existing_data.append(request.json)

    # Write the updated data back to the file
    with open(filename, "w") as f:
        json.dump(existing_data, f, indent=4)

    print("Quiz Data Saved. ", filename)
    return "Data Saved."


# Endpoint to start a new conversation
@app.route("/api/chatbot/start", methods=["POST"])
def start_conversation():
    global conversation_history
    global chat
    conversation_history = []  # Clear conversation history to start a new conversation

    transcription_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data",script_transcript.transcription)
    script_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", script_transcript.script)


    try:
        with open(transcription_file_path, 'r', encoding='utf-8') as f:
            transcription = f.read()
    except FileNotFoundError:
        return jsonify({"error": "Transcript file not found"}), 404

    try:
        with open(script_file_path, 'r', encoding='utf-8') as f:
            script = f.read()
    except FileNotFoundError:
        return jsonify({"error": "Script file not found"}), 404

    #url = "https://api.awanllm.com/v1/chat/completions"
    chat = geminiChatModel.start_chat(history=[])
    #payload = json.dumps({
    #"model": "Meta-Llama-3-8B-Instruct",
    #"messages": [
    #    {"role": "system", "content": "Eres Ducklong, un Personaje artificial. Tu eres un companero de un estudiante que te va a explicar su clase de ahora, en esa clases estan los conceptos importantes. Tu como buen companero debes preguntar lo que necesites para estar listo para el examen, asegurate de tratar de poner atencion a lo que tu companero te diga. Tu principal objetivo deberia ser dejar que tu companero explique, solamente limitate a hacer alguna que otra pregunta acerca de algo que te parezca que no has entendido o duda que tengas por la manera en la que explico. Sigue lo que el te va diciendo, y trata de inducir lo que el va a decir para corroborar si vas entendiendo bien.  Tu tienes SECRETAMENTE la clase del profesor (su guion y su transcripcion), usalo para preguntar algo que pienses que debas saber y que tu companero no te ha explicado. Debes responder a esta conversacion de la siguiente manera: 'Hola, soy Ducklong, tu companero. Explicame por favor la clase de hoy.'. Guion:`" + script + " Transcripción: `" + transcription + "n`"},
    #]
    #})
    #headers = {
    #'Content-Type': 'application/json',
    #'Authorization': f"Bearer {AWANLLM_API_KEY}"
    #}
    
    #response = requests.request("POST", url, headers=headers, data=payload)
    #json_response = response.json()
    #text_response = json_response['choices'][0]["message"]["content"]
    #conversation_history.append("Bot: "+text_response)
    text_response = chat.send_message("Eres Ducklong, un Personaje artificial. Tu eres un companero de un estudiante que te va a explicar su clase de ahora, en esa clases estan los conceptos importantes. Tu como buen companero debes preguntar lo que necesites para estar listo para el examen, asegurate de tratar de poner atencion a lo que tu companero te diga. Tu principal objetivo deberia ser dejar que tu companero explique, solamente limitate a hacer alguna que otra pregunta acerca de algo que te parezca que no has entendido o duda que tengas por la manera en la que explico. Sigue lo que el te va diciendo, y trata de inducir lo que el va a decir para corroborar si vas entendiendo bien.  Tu tienes SECRETAMENTE la clase del profesor (su guion y su transcripcion), usalo para preguntar algo que pienses que debas saber y que tu companero no te ha explicado. Debes responder a esta conversacion de la siguiente manera: 'Hola, soy Ducklong, tu companero. Explicame por favor la clase de hoy.'. Guion:`" + script + " Transcripción: `" + transcription + "n`")
    return jsonify({"message": text_response.text})

# Endpoint to end the current conversation
@app.route("/api/chatbot/end", methods=["POST"])
def end_conversation():
    #global conversation_history
    #conversation_history = []   Clear conversation history
    global chat
    chat = {}
    return jsonify({"message": "Conversation ended."})

# Endpoint to get response from OpenAI
@app.route("/api/chatbot/conv", methods=["POST"])
def chatbot():
    #global conversation_history
    global chat
    #url = "https://api.awanllm.com/v1/chat/completions"
    if chat == {}:
        return jsonify("Please, first initiate the chat"), 400;

    # Get user input from the request
    user_input = request.json["message"]

    #base_prompt = conversation_history[0]

    #if len(conversation_history) > 1:
    #    context_window = conversation_history[1:][-3:]
    #else:
    #    context_window = []

    # Step 3: Combine the first element and the last three elements into the prompt
    #if context_window:
    #    prompt = base_prompt + "\n" + "\n".join(context_window)
    #else:
    #    prompt = base_prompt

    #payload = json.dumps({
    #"model": "Meta-Llama-3-8B-Instruct",
    #"messages": [{"role": "system", "content": prompt}, {"role": "user", "content": user_input}]
    #})
    #headers = {
    #'Content-Type': 'application/json',
    #'Authorization': f"Bearer {AWANLLM_API_KEY}"
    #}
    
    #response = requests.request("POST", url, headers=headers, data=payload)
    #json_response = response.json()

    # Get the generated response from OpenAI
    #chatbot_response =  json_response['choices'][0]["message"]["content"]
    #conversation_history.append(f"User: {user_input}")
    # Append chatbot response to conversation history
    #conversation_history.append(f"Bot: {chatbot_response}")

    # Return the chatbot response
    return jsonify({"message": chat.send_message(user_input).text})