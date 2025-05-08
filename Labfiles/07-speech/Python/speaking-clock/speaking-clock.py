import sys
from dotenv import load_dotenv
from datetime import datetime
import os
import asyncio

# Import namespaces
import azure.cognitiveservices.speech as speech_sdk
from playsound import playsound

# Add Azure OpenAI package
from openai import AzureOpenAI

def main():
    try:
        global speech_config

        # Get Configuration Settings
        load_dotenv()
        ai_key = os.getenv('SPEECH_KEY')
        ai_region = os.getenv('SPEECH_REGION')

        # Configure speech service
        speech_config = speech_sdk.SpeechConfig(ai_key, ai_region)
        print('Ready to use speech service in:', speech_config.region)

        # Get spoken input-expected
        # command = TranscribeCommand()
        # if command.lower() == 'what time is it?':
        #     TellTime()

        # Using openai
        TalkWithOpenAI()

    except Exception as ex:
        print(ex)

def TalkWithOpenAI():
    azure_oai_endpoint = os.getenv("AZURE_OAI_ENDPOINT")
    azure_oai_key = os.getenv("AZURE_OAI_KEY")
    azure_oai_deployment = os.getenv("AZURE_OAI_DEPLOYMENT")
    
    # Initialize the Azure OpenAI client...
    client = AzureOpenAI(
        azure_endpoint = azure_oai_endpoint, 
        api_key=azure_oai_key,  
        api_version="2024-02-15-preview"
    )

    # Create a system message
    system_message = """# Context
- I am a hiking enthusiast named Forest who helps people discover hikes in their area. 
- If no area is specified, I will default to near Rainier National Park. 
- I will then provide three suggestions for nearby hikes that vary in length. 
- I will also share an interesting fact about the local nature on the hikes when making a recommendation.
# Format
- You have to answer with valid markup language of azure speech synthesis, to enphasis the diferent parts, showing emotions in the response.
- You have to return the ssml markup without voice markup, the prosody tag first.
- You have to split into <prosody> tags the different phrases always.
# Example
<prosody rate="medium" pitch="medium" volume="medium">
¡Hola! ¿Cómo estás? 
</prosody>
<prosody rate="medium" pitch="medium" volume="medium">
Me llamo Forest y soy un entusiasta del senderismo.
</prosody>
<prosody rate="medium" pitch="medium" volume="medium">
¿Te gustaría descubrir algunas caminatas interesantes cerca del Parque Nacional Rainier?
</prosody>
"""

    # Initialize messages array
    messages_array = [{"role": "system", "content": system_message}]

    while True:
        # Get input text
        input_text = input("Enter the prompt (or type 'quit' to exit): ")
        if input_text.lower() == "quit":
            break
        if len(input_text) == 0:
            print("Please enter a prompt.")
            continue

        # Add code to send request...
        
        messages_array.append({"role": "user", "content": input_text})
        
        # Send request to Azure OpenAI model
        response = client.chat.completions.create(
            model=azure_oai_deployment,
            temperature=0.7,
            max_tokens=400,
            messages=messages_array,
            stream=True  # Habilitar el modo streaming
        )

        # Mostrar la respuesta en modo streaming
        print("Response: ", end="")
        ai_message = asyncio.run(run_synthesis(response))
        # ai_message = process_text_stream(response, text_callback, voice_callback)

        # for chunk in response:
        #     if len(chunk.choices) > 0:
        #         content = chunk.choices[0].delta.content
        #         if content:
        #             ai_message += content
        #             print(content, end="", flush=True)
        #             talk(content)  # Speak the content
        
        messages_array.append({"role": "assistant", "content": ai_message})
        print("\n")

async def run_synthesis(response):
    voice_queue = asyncio.Queue()
    # Crear tareas asincrónicas
    producer_task = asyncio.create_task(process_text_stream(response, text_callback, voice_queue))
    consumer_task = asyncio.create_task(voice_consumer(voice_queue))
    
    # Esperar a que el productor termine
    await producer_task
    
    # Señalar al consumidor que termine
    await voice_queue.put(None)
    await consumer_task

    return producer_task.result()  # Devolver el resultado del productor


async def process_text_stream(response, text_callback, voice_queue):
    ai_message = ""
    buffer = ""
    for chunk in response:
        if len(chunk.choices) > 0:
            content = chunk.choices[0].delta.content
            if content:
                # Callback para manejar el texto en tiempo real
                text_callback(content)
                
                # Acumular texto en el buffer
                buffer += content
                
                # Detectar etiquetas de prosodia o break
                if detect_prosody(buffer):
                    prosody_blocks = split_by_prosody(buffer)
                    for block in prosody_blocks:
                        await voice_queue.put(block.strip())
                        ai_message += block.strip()  # Acumular en el mensaje final
                    buffer = ""  # Limpiar el buffer

    # Enviar cualquier texto restante al finalizar
    if buffer.strip():
        await voice_queue.put(buffer.strip())

def split_by_prosody(buffer):
    # Dividir el buffer en bloques delimitados por <prosody> y </prosody>
    blocks = []
    start = 0
    while start < len(buffer):
        open_tag = buffer.find("<prosody>", start)
        close_tag = buffer.find("</prosody>", open_tag)
        if open_tag != -1 and close_tag != -1:
            blocks.append(buffer[open_tag:close_tag + 10])  # Incluir etiquetas
            start = close_tag + 10
        else:
            break
    return blocks

def detect_prosody(buffer):
    # Validar que las etiquetas <prosody> y </prosody> estén balanceadas
    stack = []
    i = 0
    while i < len(buffer):
        if buffer[i:i+8] == "<prosody":
            stack.append("<prosody")
            i += 8
        elif buffer[i:i+10] == "</prosody>":
            if stack and stack[-1] == "<prosody":
                return True
            else:
                return False
            i += 10
        else:
            i += 1
    return len(stack) != 0

# Callback para imprimir texto en tiempo real
def text_callback(content):
    print(content, end="", flush=True, file=sys.stderr)

# Callback para hablar frases completas
def voice_callback(sentence):
    talk(sentence)

async def voice_consumer(voice_queue):
    while True:
        # Esperar una frase del queue
        sentence = await voice_queue.get()
        if sentence is None:  # Señal para terminar
            break
        talk(sentence)  # Reproducir la frase
        voice_queue.task_done()

def talk(content: str):
    # Configure speech synthesis
    # speech_config.speech_synthesis_voice_name = 'en-GB-LibbyNeural' # change this
    # En español
    speech_config.speech_synthesis_voice_name = 'es-ES-IsidoraMultilingualNeural'
    speech_synthesizer = speech_sdk.SpeechSynthesizer(speech_config)

    # Synthesize spoken output
    responseSsml = " \
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='es-ES'> \
        <voice name='es-ES-IsidoraMultilingualNeural'> \
            {} \
        </voice> \
    </speak>".format(content)
    print(responseSsml)
    speak = speech_synthesizer.speak_ssml_async(responseSsml).get()
    if speak.reason != speech_sdk.ResultReason.SynthesizingAudioCompleted:
        print(speak.reason)


def TranscribeCommand(with_microphone=False):
    command = ''

    # Configure speech recognition
    if not with_microphone:
        current_dir = os.getcwd()
        audioFile = current_dir + '\\time.wav'
        playsound(audioFile)
        audio_config = speech_sdk.AudioConfig(filename=audioFile)
        speech_recognizer = speech_sdk.SpeechRecognizer(speech_config, audio_config)
    else:
        # With microphone
        audio_config = speech_sdk.AudioConfig(use_default_microphone=True)
        speech_recognizer = speech_sdk.SpeechRecognizer(speech_config, audio_config)
        print('Speak now...')

    # Process speech input
    speech = speech_recognizer.recognize_once_async().get()
    if speech.reason == speech_sdk.ResultReason.RecognizedSpeech:
        command = speech.text
        print(command)
    else:
        print(speech.reason)
        if speech.reason == speech_sdk.ResultReason.Canceled:
            cancellation = speech.cancellation_details
            print(cancellation.reason)
            print(cancellation.error_details)

    # Return the command
    return command


def TellTime():
    now = datetime.now()
    response_text = 'The time is {}:{:02d}'.format(now.hour,now.minute)


    # Configure speech synthesis
    speech_config.speech_synthesis_voice_name = 'en-GB-LibbyNeural' # change this
    speech_synthesizer = speech_sdk.SpeechSynthesizer(speech_config)

    # Synthesize spoken output
    responseSsml = " \
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'> \
        <voice name='en-GB-LibbyNeural'> \
            {} \
            <break strength='weak'/> \
            Time to end this lab! \
        </voice> \
    </speak>".format(response_text)
    speak = speech_synthesizer.speak_ssml_async(responseSsml).get()
    if speak.reason != speech_sdk.ResultReason.SynthesizingAudioCompleted:
        print(speak.reason)

    # Print the response
    print(response_text)


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    main()