import pika
import threading
import uuid

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.exchange_declare(exchange='chat_exchange', exchange_type='topic')

current_channel = None
queue_name = None

def receive_messages(channel_name, username):
    def callback(ch, method, properties, body):
        if properties.headers['username'] != username:
            print(f"{properties.headers['username']}: {body.decode()}")

    result = channel.queue_declare(queue='', exclusive=True)
    global queue_name
    queue_name = result.method.queue

    channel.queue_bind(exchange='chat_exchange', queue=queue_name, routing_key=channel_name)
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

def send_message(channel_name, username):
    print("Digite a mensagem (ou '/trocar <número>' para alternar de chat ou 'sair' para encerrar)")
    while True:
        message = input()
        if message == 'sair':
            break
        elif message.startswith('/trocar'):
            _, new_chat_number = message.split(' ', 1)
            if new_chat_number in ['1', '2', '3', '4']:
                global current_channel, queue_name
                channel_name = f"chat.{new_chat_number}"
                print(f"Alternando para o chat {new_chat_number}")
                if current_channel:
                    channel.queue_unbind(exchange='chat_exchange', queue=queue_name, routing_key=current_channel)
                channel.queue_bind(exchange='chat_exchange', queue=queue_name, routing_key=channel_name)
                current_channel = channel_name
            else:
                print("Chat inválido.")
        else:
            properties = pika.BasicProperties(
                headers={'username': username, 'content_type': 'text/plain', 'delivery_mode': 2}
            )
            channel.basic_publish(
                exchange='chat_exchange',
                routing_key=current_channel,
                body=message,
                properties=properties
            )

def join_chat():
    print("Bem-vindo(a) ao chat!")
    print("Escolha o número do chat em que deseja participar:")
    print("1. Jogos")
    print("2. Futebol")
    print("3. Estudos")
    print("4. Fofoca")

    chat_number = input("Digite o número do chat: ")
    username = input("Digite o seu nome: ")

    if chat_number == '1':
        channel_name = 'chat.1'
    elif chat_number == '2':
        channel_name = 'chat.2'
    elif chat_number == '3':
        channel_name = 'chat.3'
    elif chat_number == '4':
        channel_name = 'chat.4'
    else:
        print("Opção inválida.")
        return

    global current_channel, queue_name
    current_channel = channel_name

    receive_thread = threading.Thread(target=receive_messages, args=(channel_name, username))
    receive_thread.daemon = True
    receive_thread.start()

    send_message(channel_name, username)

    connection.close()

join_chat()
