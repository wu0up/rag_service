# 包含組agent和ainvok agent的class

import operator
from typing import List, Dict, TypedDict, Annotated, Union
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, StateGraph
from langgraph.constants import Send

class OverallState(TypedDict):
    contents: List[str]
    summaries: Annotated[list, operator.add]
    collapsed_summaries: List[str]
    final_summary: str

class SummaryState(TypedDict):
    content: str

class SummaryAgent:
    def __init__(
        self, 
        model: str = "gpt-4o-mini", 
        temperature: float = 0,
        chunk_size: int = 1000,
        chunk_overlap: int = 100
    ):
        # Initialize the LLM
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self.total_sum_lst=[]
        # Define the map prompt
        self.map_prompt = ChatPromptTemplate.from_messages([
            ("system", "Write a concise summary of the following:\n\n{context}，請使用{context}的語言回復")
        ])
        
        # Create map chain
        self.map_chain = self.map_prompt | self.llm | StrOutputParser()
        
        # Create the StateGraph
        self.graph = StateGraph(OverallState)
        self.graph.add_node("generate_summary", self.generate_summary)
        
        # Add conditional edges and compile
        self.graph.add_conditional_edges(START, self.map_summaries, ["generate_summary"])
        self.graph.add_edge("generate_summary", END)
        self.app = self.graph.compile()

    async def split_docs(self, content:str):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        split_docs = text_splitter.split_text(content)
        return split_docs

    async def generate_summary(self, state: SummaryState):
        try:
            print(f'Processing content length: {len(state["content"])}, time: {datetime.now()}')
            response = await self.map_chain.ainvoke({"context": state["content"]})
            self.total_sum_lst.append(response)
            return {"summaries": self.total_sum_lst}
        except Exception as e:
            print(f"Error generating summary: {e}")
            return {"summaries": []}

    def map_summaries(self, state: OverallState):
        return [
            Send("generate_summary", {"content": content}) for content in state["contents"]
        ]

    async def astream(self, input_content: Union[List[str], str]):
        # 支持直接傳入字符串或文檔列表
        if isinstance(input_content, str):
            split_docs =await self.split_docs(input_content)
        else:
            split_docs =await self.split_docs(" ".join(input_content))

        summaries = []
        async for step in self.app.astream(
            {"contents": split_docs},
            {"recursion_limit": 10},
        ):
            if "generate_summary" in step:
                if 'summaries' in step.get('generate_summary'):
                    summaries = step.get('generate_summary').get('summaries')
        
        return summaries


# async def main():
#     agent = SummaryAgent(
#         model="gpt-4o-mini", 
#         temperature=0, 
#         chunk_size=1000, 
#         chunk_overlap=100
#     )

#     # 傳入字符串
#     text ="date:2024-12-04 參考資料:然後這 3 個現在是一個發散式的主題，我們可以自己決定要做什麼主題，然後盡量就 是結合我們既有的技術去做發發想，然後這邊我會就這這整個流程，這邊我會委託那 個宗翰跟。,好，這邊就是一個另外一個。,發現，找那個不見了啊，對，就是這樣子，這是人人，然後抓進去變成他，然後之後 呢，就是這個人臉跟遊客做什麼，他就對著做什麼，就把這個不靈魂變成我，然後再 來我們看我們看到第 3 個網上就是到了第 3 個那邊，第 3 個服務是到那。,然後就是現在就是這個工作的他可以就 是一張照片，然後他加一個無照的影片，然後他就可以生成旁邊，這種就是把讓圖片 動起來的影片，然後之後可以也可以用在油花那邊，就是先把股價的股片準備好，然 後圖片的話就是套那個跟亞特蘭提斯相關的。,對對對，你不能用我的。,這個東西他有什麼，如果可以幫我們設備一下然後。,把它關掉好的關掉，然後你要關係，他說，這個這個這個這個我應該沒有，他沒有開 始。,那我這邊的話是有大概去做一個流程上的自動化，那對於前端的資料來說，剛剛看到 說故事也是長這樣子，因為那。,呃，對可以去，但是說格式的話還是要先知 道，嗯，然後去我們最近在談說有一個另外一個團隊，他們在二樓啊，他們做的那個 服務很厲害，是可以，你跟他講完之後，他會幫你把簡報做完這個簡報呢？,最後自己去運作的一個每天的一個爬蟲，它的爬蟲是這樣，就是每天呢，它就會中整 說近期有什麼新聞有什麼趨勢，那他會按照一個簡報的格式，我們做簡報，常都會有 什麼背景，那別人的說法跟有沒有一些下案例，那我們的看法等等的還有這種標頭。,那其實他這邊的話我就會說，我就會下說，請他幫我把傳入的資料把使用者的請求， 然後轉換成傳入資料的那個報告格式這樣，那他當然是沒有辦法。,格式是完全一樣 的，但是他可能可以有一個他的。,是帶新的書對，但是它就是起點不，現在也是一樣，就是不可以傳太多，不然會有那 個欸，傳太多其實也沒差，但是就會比較等比較久而已，所以之前是要到資料庫一個 個上傳，現在變得很像 gpt 一樣嘛，在聊天界面就可以上傳了。,對，但是就是只能傳一個那上傳答案會存在的不是資料庫啊，不會，他這次我們專家 就沒了對，而且這個傳的話就是，如果你的答案太大，比如說你有 20 幾頁的話，我們 這邊會先去把它做一個 summary，然後才送給 gpt，所以可能會得比較久，所以我們 這邊自己內部會去做整理，然後之後才會去對對對對對，因為他的。,124 那個。,他就是可以去做一個。,有沒有在。,對對。,那如果偵測有 問題的話，它可能就會回覆，那這時候它就直接打 API 方式或者是其他 website，無論 再傳給前端，然後這時候就是那個前端的應用介面，它收到之後，它就會再把文字轉 語音就直接出生，他們那個系統有點類似這個樣子。,什麼工具啊，還是什麼你就可以用這種方式很快做，那之後你也會很多 sales key 的那 個都要出來啊。"
#     summary_str = await agent.astream(text)
#     print("Summary from string:", len(summary_str), len(summary_str[0]))

# if __name__ == "__main__":
#     import os

#     api_key = "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"

#     os.environ["OPENAI_API_KEY"] = api_key
#     import asyncio
#     asyncio.run(main())