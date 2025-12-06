import atexit
from llama_cpp import Llama, LlamaTokenizer
from mailbot_logging import Logger

class transformer:
    def __init__(self, model_params: dict[str, str], max_output_tokens=255):
        try:
            self.logger = Logger(self)
            
            self.model_params = model_params
            self.model = Llama(**model_params)
            self.tokenizer = LlamaTokenizer(self.model)
            self.max_output_tokens = max_output_tokens

            # Estimate reserved tokens (use placeholder name)
            self.reserved_tokens = self.token_count(self.INSTRUCT_HEADER.format('user')) + self.token_count(self.ASSISTANT_TAG) + max_output_tokens

        except Exception as e:
            print(f"Failed to setup model: {e}")
            exit(3)
            
    def close(self):
        try:
            # Release resource allocation
            del self.model
            del self.tokenizer
        except Exception as e:
            self.logger.error("Failed to free resources", e)