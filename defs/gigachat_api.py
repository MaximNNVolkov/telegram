from decouple import config
from langchain.schema import HumanMessage, SystemMessage
from langchain_gigachat import GigaChat
import datetime
from typing import Optional


_giga: Optional[GigaChat] = None


def get_giga_client() -> GigaChat:
    global _giga
    if _giga is not None:
        return _giga

    auth = str(config('SBER_AUTH', default='')).strip()
    if not auth:
        raise RuntimeError('SBER_AUTH is not set.')

    _giga = GigaChat(
        credentials=auth,
        model='GigaChat',
        verify_ssl_certs=False,
    )
    return _giga

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
    giga = get_giga_client()
    if start_first_msg:
        print(start_first_msg, datetime.datetime.utcnow() - datetime.timedelta(minutes=10),
              start_first_msg < datetime.datetime.utcnow() - datetime.timedelta(minutes=10))
        if start_first_msg < datetime.datetime.utcnow() - datetime.timedelta(minutes=10):
            msgs = [SystemMessage(content=role)]
    else:
        start_first_msg = datetime.datetime.utcnow()
        msgs = [SystemMessage(content=role)]
    print(start_first_msg, user_msg)
    start_first_msg = datetime.datetime.utcnow()
    msgs.append(HumanMessage(content=user_msg))
    answer = giga(msgs)
    msgs.append(answer)
    print(answer.content)
    return answer.content
