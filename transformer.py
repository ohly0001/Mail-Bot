import atexit
from llama_cpp import Llama, LlamaTokenizer

class ai_controller:
    INSTRUCT_HEADER = "### instruction: You are a helpful email correspondent. Avoid greetings unless the user wrote one. The person you are replying to is {}."
    ASSISTANT_TAG = '### assistant: '
    USER_TAG = '### user: '
    BOT_GMAIL_NAME = 'email bot'

    def __init__(self, model_params: dict[str, str], max_output_tokens=255):
        try:
            self.model_params = model_params
            self.model = Llama(**model_params)
            self.tokenizer = LlamaTokenizer(self.model)
            self.max_output_tokens = max_output_tokens

            # Estimate reserved tokens (use placeholder name)
            self.reserved_tokens = self.token_count(self.INSTRUCT_HEADER.format('user')) + self.token_count(self.ASSISTANT_TAG) + max_output_tokens
            atexit.register(self.close)

        except Exception as e:
            print(f"Failed to setup model: {e}")
            exit(3)

    def token_count(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def __call__(self, msg_stack: list[dict[str, str]]):
        if not msg_stack:
            return None

        sender_name = msg_stack[-1]["sender_name"]
        instruction_msg = self.INSTRUCT_HEADER.format(sender_name)
        total_tokens = self.reserved_tokens
        conversation_stack = [instruction_msg]

        # newest last
        for msg in reversed(msg_stack):
            encoded = self.token_count(msg['body_text'])
            if total_tokens + encoded > self.model_params['n_ctx']:
                break
            total_tokens += encoded

            tag = self.USER_TAG if msg["sender_name"] != self.BOT_GMAIL_NAME else self.ASSISTANT_TAG
            conversation_stack.append(f"{tag}{msg['body_text']}")

        conversation_stack.append(self.ASSISTANT_TAG)
        prompt_str = '\n'.join(conversation_stack)

        rsp = self.model(prompt_str, max_tokens=self.max_output_tokens)
        rsp_str = rsp['choices'][0]['text']

        if '### user:' in rsp_str:
            rsp_str = rsp_str.split('### user:', 1)[0]

        return rsp_str.strip()

    def close(self):
        try:
            del self.model
            del self.tokenizer
        except Exception as e:
            print(f"Failed to dispose of model: {e}")
