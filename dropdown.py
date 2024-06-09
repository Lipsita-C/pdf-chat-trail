import gradio as gr
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import FunctionCallingAgentWorker
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from gradio_pdf import PDF
from pdf2image import convert_from_bytes
import chromadb
import pandas  as pd


from llama_index.llms.anthropic import Anthropic
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_parse import LlamaParse
from llama_index.core import Settings
import os
import openai
from dotenv import load_dotenv
from supabase import create_client, Client
from src.utils import utils , draft
#from llama_index.retrievers.bm25 import BM25Retriever

load_dotenv()
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
#LLAMA_CLOUD_API_KEY=os.getenv("LLAMA_CLOUD_API_KEY")

url=os.environ.get("SUPABASE_URL")
key=os.environ.get("SUPABASE_KEY")                         
supabase=create_client(url, key)

openai.api_key = OPENAI_API_KEY
Utilities = utils()
Draft = draft()
        
list_indexes_tab = gr.Interface(
    fn= Utilities.print_indexes, inputs=[], outputs=gr.Dataframe(headers=["Title"], datatype=['str'], label='Output'), title="Find the existing Documents to search from...", allow_flagging='never')


#converse_with_pdf_tab = gr.ChatInterface( fn=Utilities.converse_pdf, additional_inputs=[gr.Dropdown(choices=Utilities.print_indexes_tuple(), label='Select the Collection')] ,additional_inputs_accordion=gr.Accordion(label="Mandatory Fields", open=True), title="Converse with Index",  chatbot=gr.Chatbot(
#            height=500))

# def call_dd():

#     return gr.Dropdown(Utilities.print_indexes_tuple())

# converse_with_pdf_tab = gr.Blocks()
# with converse_with_pdf_tab:
#     chatbot = gr.Chatbot()
#     msg = gr.Textbox(label="Ask Questions")
#     with gr.Row():
#         clear = gr.ClearButton([msg, chatbot])
#         refresh_btn = gr.Button("Refresh Collections", variant='primary')
#     dd_btn = gr.Dropdown(choices=Utilities.print_indexes_tuple(), label='Select the Collection')
#     refresh_btn.click(call_dd, [], [dd_btn])
    
#     msg.submit(Utilities.converse_pdf, [msg, chatbot, dd_btn], [msg, chatbot])
def call_dd():

    return gr.Dropdown(Utilities.print_indexes_tuple())

converse_with_pdf_tab = gr.Blocks()
with converse_with_pdf_tab:
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Ask Questions")
    with gr.Row():
        clear = gr.ClearButton([msg, chatbot])
        refresh_btn = gr.Button("Refresh Collections", variant='primary')
    dd_btn = gr.Dropdown(choices=Utilities.print_indexes_tuple(), label='Select the Collection')
    refresh_btn.click(call_dd, [], [dd_btn])
    
    msg.submit(Utilities.converse_pdf, [msg, chatbot, dd_btn], [msg, chatbot])


# TO DO
# MAKE SURE TO FIX THE GENERATE BUTTON WITH DROPDOWN
# GET THE Utiiities.print_indexes() inside a wrapper function
# add logot button


create_indexes_tab = gr.Interface(
    fn= Utilities.index_pdf,
    inputs=["file"],
    outputs="text",
    title="Index The PDF",
    description="Chat with a PDF file and ask questions related to it.\n \
                    Please limit your file to 50 pages."
)



# delete_index_tab = gr.Blocks() 
# with delete_index_tab :
#     gr.Markdown(
#         """
#     # Delete Collection if not using.
#     Select the Index from Dropdown
#     """
#     )
#     with gr.Row():
#         gr.Button("Log Out", link = "/logout")
#     # with gr.Row():

#     #     del_input = gr.Dropdown(choices=call_dd(), label='Select the Collection')
#     #     del_output = gr.Textbox()
    
#     # with gr.Row():
#     #     btn = gr.Button("Refresh Collections", variant='primary')
#     #     del_button = gr.Button("Delete", variant='stop')

#     # del_button.click(Utilities.del_index, inputs=[del_input], outputs=del_output)
    
#     # btn.click(call_dd, [], [del_input])
#     with gr.Row():

 
#         del_output = gr.Textbox()
        
#     with gr.Row():
#         btn = gr.Button("Refresh Collections", variant='primary')
#         del_button = gr.Button("Delete", variant='stop')

#     del_button.click(Utilities.del_index, inputs=[], outputs=del_output)
    
#     btn.click(call_dd, [], [])


delete_index_tab = gr.Blocks() 
with delete_index_tab :
    gr.Markdown(
        """
    # Delete Collection if not using.
    Select the Index from Dropdown
    """
    )
    with gr.Row():
        del_input = gr.Dropdown(choices=Utilities.print_indexes_tuple(), label='Select the Collection')
        del_output = gr.Textbox()
    
    with gr.Row():
        btn = gr.Button("Refresh Collections", variant='primary')
        del_button = gr.Button("Delete", variant='stop')

    del_button.click(Utilities.del_index, inputs=[del_input], outputs=del_output)
    
    btn.click(call_dd, [], [del_input])



demo = gr.TabbedInterface([ list_indexes_tab, create_indexes_tab, converse_with_pdf_tab, delete_index_tab], [ "List Collections", "Create New Collection", "Converse with Collection", "Delete collection"])

# Launch the interface
demo.launch(auth=Utilities.get_creds(), auth_message="Provide Username and password", max_file_size="10mb")
#demo.launch( max_file_size="20mb")
