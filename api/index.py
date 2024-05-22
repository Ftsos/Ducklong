from datetime import date
import json
import os
import requests
from flask import Flask, request, jsonify;
from pydantic import BaseModel
from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from faster_whisper import WhisperModel
from celery.result import AsyncResult
from types import SimpleNamespace
from celery import Celery
from openai import OpenAI
from flask_cors import CORS


client = OpenAI(api_key='sk-proj-p9ruNmMSCGV4LESKQJYPT3BlbkFJV2ewry7C2PthrlsVLdkK')
AWANLLM_API_KEY = '3657a1e9-38a1-4295-8a48-c97c73084ca4'

conversation_history = []

script_transcript =  SimpleNamespace(script='', transcription='')



app = Flask(__name__)
CORS(app)
whisper_model_size = "large-v3"
app.config['CELERY_BROKER_URL'] = 'redis://default:kqPNtC4dM5sZyd3iCXRWayDM9KsoHWrr@kqPNtC4dM5sZyd3iCXRWayDM9KsoHWrr/0' 
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])

class QuestionFormat(BaseModel):
    query: str
    choices: list
    answer: int

tokenizer = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2")

@celery.task
def transcribe_audio_file(audio_file): 
    model = WhisperModel(whisper_model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(audio_file, beam_size=5, language="es")
    transcription = []
    print("Transcription in progress")
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
        transcription.append("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

    output_file = os.path.join(os.makedirs("data", exist_ok=True), os.path.basename(audio_file) + "-trans.txt")
    with open(output_file, 'w') as f:
        f.write('\n'.join(transcription))

    return os.path.basename(audio_file) + "-trans.txt"

hf_pipeline = pipeline('text-generation', model=model, tokenizer=tokenizer, device_map='auto')

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

    parser = JsonSchemaParser(QuestionFormat.schema())
    prefix_function = build_transformers_prefix_allowed_tokens_fn(tokenizer, parser)

    # Generate the output with the prefix function
    output = hf_pipeline(prompt, max_new_tokens=200, num_return_sequences=1, return_full_text=False, prefix_allowed_tokens_fn=prefix_function)[0]['generated_text']
    
    # Clean and parse the generated text
    cleaned_text = output.replace('\n', '').replace('\\', '')
    
    try:
        # Save the cleaned text to a file
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quizzes", "questions.json")
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(cleaned_text)
        
        # Parse the cleaned JSON text
        questions_json = json.loads(cleaned_text)
        return jsonify(questions_json)
    except json.JSONDecodeError as e:
        return jsonify({"error": "Invalid JSON format", "details": str(e)}), 500

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
def get_file():

    if 'transcription' not in request.files or 'script' not in request.files:
        return jsonify({"error": "Both files must be provided"}), 400

    transcription = request.files['transcription']
    script = request.files['script']

    if transcription.filename != '':
        transcription.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), transcription.filename))

    if script.filename != '':
        script.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), script.filename))

    result = transcribe_audio_file.delay(transcription.filename)    
    return jsonify({"message": "Transcription process started", "task_id": result.id}), 202


@app.route("/api/quiz/get/<task_id>/<load_if_yes>", methods=['GET'])
def check_transcription_status(task_id, load_if_yes):
    # Check the status of the transcription task
    task = AsyncResult(task_id)

    if task.state == 'PENDING':
        # Task is still pending
        return jsonify({"status": "pending"}), 202
    elif task.state == 'SUCCESS':
        # Task is complete, return the result
        if(load_if_yes):
            script_transcript.transcription = task.get()
        return jsonify({"status": "complete", "result": task.get()}), 200
    else:
        # Task has failed or been revoked
        return jsonify({"status": "error", "message": "Transcription task failed or revoked"}), 500

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
@app.route("/chatbot/start", methods=["POST"])
def start_conversation():
    global conversation_history
    conversation_history = []  # Clear conversation history to start a new conversation

    transcription_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_transcript.transcription)
    script_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_transcript.script)


    try:
        with open(transcription_file_path, 'r') as f:
            transcription = f.read()
    except FileNotFoundError:
        return jsonify({"error": "Transcript file not found"}), 404

    try:
        with open(script_file_path, 'r') as f:
            script = f.read()
    except FileNotFoundError:
        return jsonify({"error": "Script file not found"}), 404


    response = client.completions.create(engine="davinci",  # You can try other engines too
    prompt="Eres Ducklong, un Personaje artificial. Tu eres un companero de un estudiante que te va a explicar su clase de ahora, en esa clases estan los conceptos importantes. Tu como buen companero debes preguntar lo que necesites para estar listo para el examen, asegurate de tratar de poner atencion a lo que tu companero te diga. Tu principal objetivo deberia ser dejar que tu companero explique, solamente limitate a hacer alguna que otra pregunta acerca de algo que te parezca que no has entendido o duda que tengas por la manera en la que explico. Sigue lo que el te va diciendo, y trata de inducir lo que el va a decir para corroborar si vas entendiendo bien.  Tu tienes SECRETAMENTE la clase del profesor (su guion y su transcripcion), usalo para preguntar algo que pienses que debas saber y que tu companero no te ha explicado. Debes responder a esta conversacion de la siguiente manera: 'Hola, soy Ducklong, tu companero. Explicame por favor la clase de hoy.'. Guion:`" + script + " Transcripción: `" + transcription + "n`",
    max_tokens=150)  # Adjust max_tokens as per your requirement)
    return jsonify({"message": response})

# Endpoint to end the current conversation
@app.route("/end", methods=["POST"])
def end_conversation():
    global conversation_history
    conversation_history = []  # Clear conversation history
    return jsonify({"message": "Conversation ended."})

# Endpoint to get response from OpenAI
@app.route("/chatbot/conv", methods=["POST"])
def chatbot():
    global conversation_history

    # Get user input from the request
    user_input = request.json["message"]

    # Append user input to conversation history
    conversation_history.append(f"User: {user_input}")

    # Generate prompt by concatenating conversation history
    prompt = "\n".join(conversation_history[-3:])  # Consider last 3 exchanges
    prompt += "\nBot:"

    # Call OpenAI API to get chatbot response
    response = client.completions.create(engine="davinci",  # You can try other engines too
    prompt=prompt,
    max_tokens=150)  # Adjust max_tokens as per your requirement)

    # Get the generated response from OpenAI
    chatbot_response = response.choices[0].text.strip()

    # Append chatbot response to conversation history
    conversation_history.append(f"Bot: {chatbot_response}")

    # Return the chatbot response
    return jsonify({"message": chatbot_response})