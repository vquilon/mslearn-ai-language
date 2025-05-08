from dotenv import load_dotenv
import os

# Import namespaces
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

def main():
    # Se limina el contenido de la consol previa
    os.system('cls' if os.name == 'nt' else 'clear')

    # Get Configuration Settings
    load_dotenv()
    ai_endpoint = os.getenv('AI_SERVICE_ENDPOINT')
    ai_key = os.getenv('AI_SERVICE_KEY')

    # Create client using endpoint and key
    credential = AzureKeyCredential(ai_key)
    ai_client = TextAnalyticsClient(endpoint=ai_endpoint, credential=credential)

    # Analyze each text file in the reviews folder
    reviews_folder = 'reviews'
    for file_name in os.listdir(reviews_folder):
        # Read the file contents
        print('\n-------------\n' + file_name)
        text = open(os.path.join(reviews_folder, file_name), encoding='utf8').read()
        print('\n' + text)

        # Get language
        detected_language = ai_client.detect_language(documents=[text])[0]
        print('\nLanguage: ' + detected_language.primary_language.name + ' (' + detected_language.primary_language.iso6391_name + ')')

        # Get sentiment
        sentiment = ai_client.analyze_sentiment(documents=[text])[0]
        print('\nSentiment: ' + sentiment.sentiment)

        # Get key phrases
        key_phrases = ai_client.extract_key_phrases(documents=[text])[0].key_phrases
        if len(key_phrases) > 0:
            print("\nKey Phrases:")
            for phrase in key_phrases:
                print('\t{}'.format(phrase))

        # Get entities
        entities = ai_client.recognize_entities(documents=[text])[0].entities
        if len(entities) > 0:
            print("\nEntities:")
            for entity in entities:
                print('\t{}: {}'.format(entity.text, entity.category))


        # Get linked entities
        entities = ai_client.recognize_linked_entities(documents=[text])[0].entities
        if len(entities) > 0:
            print("\nLinks")
            for linked_entity in entities:
                print('\t{} ({})'.format(linked_entity.name, linked_entity.url))


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()