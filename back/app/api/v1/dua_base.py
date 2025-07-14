from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
import os

def crear_llm():
    """Configuración básica del modelo de lenguaje"""
    return AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)
def crear_cadena(prompt_sistema, prompt_humano):
    llm = crear_llm()
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(prompt_sistema),
        HumanMessagePromptTemplate.from_template(prompt_humano)
    ])
    return LLMChain(llm=llm, prompt=prompt)