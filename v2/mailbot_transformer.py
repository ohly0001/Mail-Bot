import atexit
from llama_cpp import Llama, LlamaTokenizer
from mailbot_logging import Logger

class Transformer:
    INSTRUCT_HEADER = "### instruction: You are a cheerful and helpful email correspondent. Avoid greetings unless the user wrote one. The person you are replying to is {}."
    ASSISTANT_TAG = '### assistant: '
    USER_TAG = '### user: '
    BOT_GMAIL_NAME = 'email bot'

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
            
    def token_count(self, text: str) -> int:
        return len(self.tokenizer.encode(text))
            
    def close(self):
        try:
            # Release resource allocation
            del self.model
            del self.tokenizer
        except Exception as e:
            self.logger.error("Failed to free resources", e)