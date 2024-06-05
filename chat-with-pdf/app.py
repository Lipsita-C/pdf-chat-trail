import gradio as gr
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import FunctionCallingAgentWorker
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from gradio_pdf import PDF
from pdf2image import convert_from_bytes
import chromadb


from llama_index.llms.anthropic import Anthropic
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_parse import LlamaParse
from llama_index.core import Settings
import os
import openai
from dotenv import load_dotenv

load_dotenv()
ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
LLAMA_CLOUD_API_KEY=os.getenv("LLAMA_CLOUD_API_KEY")



openai.api_key = OPENAI_API_KEY




def pdf_to_text(pdf_file):

   

    # parser = LlamaParse(api_key= os.getenv("LLAMA_CLOUD_API_KEY"), result_type="markdown" )
    # initialize client, setting path to save data
    db = chromadb.PersistentClient(path="./chroma_db")
    col_exists = True
    try:
        coll =  db.get_collection(os.path.basename(pdf_file))
    except:
        col_exists = False

    if not col_exists:
        print("Collection Missing")
        # Pdf to markdown
        parser = LlamaParse(api_key=LLAMA_CLOUD_API_KEY, result_type="markdown" )
        file_extractor = {".pdf": parser}
        documents = SimpleDirectoryReader(input_files=[pdf_file], file_extractor=file_extractor).load_data()
        print(documents)

        chroma_collection = db.get_or_create_collection(os.path.basename(pdf_file))
        # assign chroma as the vector_store to the context
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
         # create your index
        index = VectorStoreIndex.from_documents(
                documents, storage_context=storage_context)
        return index
    else:
        print("Collection Exists")
        chroma_collection = db.get_or_create_collection(os.path.basename(pdf_file))
        # assign chroma as the vector_store to the context
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
         # create your index
        index = VectorStoreIndex.from_vector_store(
                 vector_store, storage_context=storage_context)
        return index


def chat_with_pdf(pdf_file, query):
    
    index_mtar = pdf_to_text(pdf_file)
    print(index_mtar)

    llm_anthropic = Anthropic(model="claude-3-opus-20240229", api_key = ANTHROPIC_API_KEY)
    

    query_engine_jp = index_mtar.as_query_engine(llm=llm_anthropic)
    query_engine_tool = QueryEngineTool(
        query_engine = query_engine_jp,
        metadata = ToolMetadata(
            name = "jpmorgan_annualreport-2022",
            description=(
                "Provided with Annual Report 2022 of JP Morgan."
                "Ask questions as text and get an answer"
            ),

        ),
    )


    agent_worker = FunctionCallingAgentWorker.from_tools(
        [query_engine_tool], llm=llm_anthropic, verbose=True)
    

    agent = agent_worker.as_agent()

    response = agent.chat(query)
    print(str(response))

    return response



demo = gr.Interface(
    fn= chat_with_pdf,
    inputs=["file", "text"],
    outputs="text",
    title="Chat with PDF",
    description="Chat with a PDF file and ask questions related to it."
)

# Launch the interface
demo.launch()