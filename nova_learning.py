from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

# Create a chatbot instance with real-time learning
chatbot = ChatBot('NOVA', storage_adapter='chatterbot.storage.SQLStorageAdapter')

# Train NOVA using a corpus of conversational data
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train('chatterbot.corpus.english')

# Allow NOVA to learn from the user in real-time
def learn_from_user(input_text):
    response = chatbot.get_response(input_text)
    print(f"NOVA: {response}")
    return response
