import gradio as gr
import chromadb
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_parse import LlamaParse
from supabase import create_client
from dotenv import load_dotenv


load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
LLAMA_CLOUD_API_KEY=os.getenv("LLAMA_CLOUD_API_KEY")
# CONVERSATION_LIMITS=int(os.environ.get("CONVERSATION_LIMITS"))
COLLECTION_LIMIT=int(os.environ.get("COLLECTION_LIMIT"))

class utils:
    db = chromadb.PersistentClient(path="./chroma_db")

    #opts = ClientOptions().replace(schema=os.environ.get("SUPABASE_SCHEMA"))
    
    supabase = create_client(url, key)


    def print_indexes(self,request: gr.Request):
        # print(request)

        response = self.supabase.table('collections').select('collection_name').eq('user', request.username).execute()
        #print(request.username)
        if not response.data:
            return []
        else:
            collection_names =  [[collection['collection_name']] for collection in response.data]
            #collection_names =  [[collection.collection_name] for collection in response.data]

        #collection_list = self.db.list_collections()
        #collection_names = [[collection.name] for collection in collection_list]
            return collection_names 

    def print_indexes_tuple(self):
        collection_list = self.db.list_collections()
        collection_names = [(collection.name,collection.name) for collection in collection_list]
        print(collection_names)
        return collection_names


    # def print_indexes_tuple(self , user: gr.Request):
    #     print(user)
    #     response = self.supabase.table('collections').select('collection_name').eq('user', user.username).execute()
    #     print(user.username)
    #     if not response.data:
    #         return []
    #     else:
    #         collection_names = [(collection['collection.name'],collection['collection.name']) for collection in response.data]
        
    #         return collection_names

    
    def del_index(self, item, request: gr.Request):
        msg = None
        user = request.username
        try:
            coll =  self.db.get_collection(item)
            print(item)
            #
            res = self.supabase.table('collections').select('user').eq('collection_name', item).execute()
            print(res)
            if len(res.data) >0 and res.data[0].get('user') == user:
                print("Correct User")
                self.db.delete_collection(name=item)
                self.supabase.table('collections').delete().eq('collection_name', item).execute()
                msg = "Deleted "+item+" successfully!!"
            else:
                 msg = "Collection  "+item+" does not belong to you, Cannot Delete!!"
        except Exception as error:
            print("An exception occurred:", error) 
            msg = "Collection "+item+" does not exist!!"
        return msg
    
    def index_pdf(self,pdf_file, request: gr.Request):
        print("Inside Index_pdf ")
        try:
            self.pdf_to_index(pdf_file, request)
            return "Collection Created Successfully by name: "+os.path.basename(pdf_file)
        except Exception as e:
            print(e)
            return "Collection Limit of "+ str(COLLECTION_LIMIT)+ " reached"

    
    def pdf_to_index(self, pdf_file, request):
        col_exists = True
        print("Inside pdf_to_index")
        try:
            coll =  self.db.get_collection(os.path.basename(pdf_file))
        except:
            col_exists = False

        print(col_exists)
        if not col_exists:  
            print("Collection Missing")
            user = request.username
            print("Is error in this line... for "+ user)
            response = self.supabase.table('collections').select('collection_name', count= 'exact').eq('user', user).execute()
            print("Response-------"+str(response))
            user_collection_count=0
            if not response.data:
                user_collection_count=0
            else:
                user_collection_count=int(response.count)
            print(user_collection_count)
            if user_collection_count<= COLLECTION_LIMIT:
                
                # Pdf to markdown
                parser = LlamaParse(api_key=LLAMA_CLOUD_API_KEY, result_type="markdown" )
                file_extractor = {".pdf": parser}
                documents = SimpleDirectoryReader(input_files=[pdf_file], file_extractor=file_extractor).load_data()
                #print("Doc----"+str(documents))

                chroma_collection = self.db.get_or_create_collection(os.path.basename(pdf_file))
                # assign chroma as the vector_store to the context
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                storage_context = StorageContext.from_defaults(vector_store=vector_store)
                # create your index
                index = VectorStoreIndex.from_documents(
                        documents, storage_context=storage_context)
                
                data, count = self.supabase.table('collections').insert([{ "user": user, "collection_name": os.path.basename(pdf_file)}]).execute()
                print("Done .....")

                return index
            else:
                raise Exception("Collection Limit Reached")
        else:
            print("Collection Exists")
            chroma_collection = self.db.get_or_create_collection(os.path.basename(pdf_file))
            # assign chroma as the vector_store to the context
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            # create your index
            index = VectorStoreIndex.from_vector_store(
                    vector_store, storage_context=storage_context)
            return index    
        

    def chat_with_collection(self,base_index, message):
    
        base_engine = base_index.as_query_engine(similarity_top_k=4)

        response = base_engine.query(message)
        #print(str(response))
        return str(response)

    def converse_pdf(self, message, history, additional_data, request: gr.Request ):
        user = request.username
        print(user)
        response = self.supabase.table('conversation_limits').select('conversation_limits').eq('user', user).execute()
        print(response)
        curr_conv_count = response.data[0].get('conversation_limits')

        if(curr_conv_count >0):
        
            if(additional_data is None):
                return "Please select the Collection in the below Dropdown"
            #print(additional_data)
            chroma_collection = None
            try:
                chroma_collection = self.db.get_collection(additional_data)
            except:
                return "Collection Missing, Please Enter the Collection Name correctly"
            
            res = self.supabase.table('collections').select('user').eq('collection_name', additional_data).execute()
            print(res)
            if len(res.data) >0 and res.data[0].get('user') == user:

                # assign chroma as the vector_store to the context
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                storage_context = StorageContext.from_defaults(vector_store=vector_store)
                # create your index
                base_index = VectorStoreIndex.from_vector_store(
                            vector_store, storage_context=storage_context)
                history.append((message, self.chat_with_collection(base_index, message) ))

                # Decrement Conversations Limit
                response = self.supabase.table('conversation_limits').select('id', 'conversation_limits').eq('user', user).execute()
                #print(response)
                row_id = response.data[0].get('id')
                limit = response.data[0].get('conversation_limits')
                self.supabase.table('conversation_limits').update({'conversation_limits': limit-1}).eq('id',row_id ).execute()

                # Write to collections
                self.supabase.table('queries_on_collection').insert([{ "user": user, "query": message, "collection_name": additional_data }]).execute()

                return "",history
            else:
                return "Collection does not belong to you. Please select your Collection", history
        else:
            return "Conversation Quota Reached. Talk to admin", history
    
    def get_creds(self):
        data = eval(os.getenv("ORG_USERS"))
        tuples_only = [value for values in data.values() for value in values if isinstance(value, tuple)]
        return tuples_only
    
class draft:

    supabase = create_client(url, key)

    def return_fn(fn):
        return fn
