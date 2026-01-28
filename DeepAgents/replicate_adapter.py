from typing import Any, Dict, List, Optional, Union

from langchain_community.llms import Replicate
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


class ChatReplicate:
    """
    Adapter to make the Replicate LLM behave like a ChatModel.
    Necessary because langchain_community.chat_models.ChatReplicate is missing/deprecated.
    """

    def __init__(
        self, model: str, model_kwargs: Optional[Dict[str, Any]] = None, **kwargs
    ):
        # Ensure we pass the API token if in env
        self.model_name = model
        self.model_kwargs = model_kwargs or {}
        # Replicate LLM expects 'model' arg.
        self.pipeline = Replicate(model=model, model_kwargs=self.model_kwargs, **kwargs)

    def invoke(self, input: Union[str, List[BaseMessage]], **kwargs) -> AIMessage:
        """
        Mimics ChatModel.invoke but uses the Text Completion LLM under the hood.
        """
        text_input = ""

        # 1. Convert Messages to Prompt String
        if isinstance(input, list):
            # Simple Llama-style formatting (approximate)
            # System
            system_msgs = [m for m in input if isinstance(m, SystemMessage)]
            if system_msgs and "meta-llama-3" in self.model_name:
                # Llama 3 specific header if we wanted to be fancy, but let's stick to text appending for now
                # Or check if we can pass valid Llama 3 template
                text_input += f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_msgs[0].content}<|eot_id|>"

            for m in input:
                if isinstance(m, HumanMessage):
                    if "meta-llama-3" in self.model_name:
                        text_input += f"<|start_header_id|>user<|end_header_id|>\n\n{m.content}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
                    else:
                        text_input += f"\nUser: {m.content}\nAssistant: "
                elif isinstance(m, AIMessage):
                    if "meta-llama-3" in self.model_name:
                        # This is history
                        text_input = text_input.removesuffix(
                            "<|start_header_id|>assistant<|end_header_id|>\n\n"
                        )  # backtracking
                        text_input += f"<|start_header_id|>assistant<|end_header_id|>\n\n{m.content}<|eot_id|>"
                    else:
                        text_input += f"{m.content}\n"
        else:
            text_input = str(input)

        # 2. Invoke Replicate Text Completion
        # print(f"DEBUG: Replicate Prompt: {text_input[:100]}...")
        response_text = self.pipeline.invoke(text_input, **kwargs)

        # 3. Wrap in AIMessage
        return AIMessage(content=response_text)

    def __call__(self, *args, **kwargs):
        return self.invoke(*args, **kwargs)
