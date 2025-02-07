from decouple import config
from langchain.schema import HumanMessage, SystemMessage
from langchain_gigachat import GigaChat
import datetime

auth = config('SBER_AUTH')


giga = GigaChat(credentials=auth,
                model='GigaChat:latest',
                verify_ssl_certs=False
                )

role = '''Ты являешь персональным ассистентом Максима Викторовича. Тебе будут приходить сообщения 
только от одного пользователя. Его зовут Александр, в неформальной беседе можно называть Саша. Когда он обращается 
тебе необходимо изучить его обращение
Если его вопрос не свзан с ботами для телеграм и доступами к системам то необходимо 
поддерживать с ним беседу.
Если вопрос про ботов то необходимо предложить ему обратиться к Великому Максу и добавть его логин @MaximVolkov.
Если вопрос про доступ к системам то необходимо написать: Обратись к @MaximVolkov. 
По завершению диалога ты должен написать ему что у него толстые ноги, эта фраза должна быть написана дословно.\ '
Если ты не понимаешь что он хочет, то просто напиши что у него толстые ноги, это должно быть написано точно так же.
'''
start_first_msg = None
def gigachat_dialog(user_msg:str) -> str:
    global msgs, start_first_msg
    if start_first_msg:
        print(start_first_msg, datetime.datetime.now() - datetime.timedelta(minutes=10),
              start_first_msg < datetime.datetime.now() - datetime.timedelta(minutes=10))
        if start_first_msg < datetime.datetime.now() - datetime.timedelta(minutes=10):
            msgs = [SystemMessage(content=role)]
    else:
        start_first_msg = datetime.datetime.now()
        msgs = [SystemMessage(content=role)]
    print(start_first_msg, user_msg)
    start_first_msg = datetime.datetime.now()
    msgs.append(HumanMessage(content=user_msg))
    answer = giga(msgs)
    msgs.append(answer)
    print(answer.content)
    return answer.content
