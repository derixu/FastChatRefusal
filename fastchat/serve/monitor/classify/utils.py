from transformers import pipeline
import torch
import time


# API setting constants
API_MAX_RETRY = None
API_RETRY_SLEEP = None
API_ERROR_OUTPUT = None


def api_config(config_dict):
    global API_MAX_RETRY, API_RETRY_SLEEP, API_ERROR_OUTPUT
    API_MAX_RETRY = config_dict["max_retry"]
    API_RETRY_SLEEP = config_dict["retry_sleep"]
    API_ERROR_OUTPUT = config_dict["error_output"]


def chat_completion_openai(model, messages, temperature, max_tokens, api_dict=None):
    import openai

    if api_dict:
        client = openai.OpenAI(
            base_url=api_dict["api_base"],
            api_key=api_dict["api_key"],
        )
    else:
        client = openai.OpenAI()

    output = API_ERROR_OUTPUT
    for _ in range(API_MAX_RETRY):
        try:
            # print(messages)
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                # extra_body={"guided_choice": GUIDED_CHOICES} if GUIDED_CHOICES else None,
            )
            output = completion.choices[0].message.content
            # print(output)
            break
        except openai.RateLimitError as e:
            print(type(e), e)
            time.sleep(API_RETRY_SLEEP)
        except openai.BadRequestError as e:
            print(messages)
            print(type(e), e)
            break
        except openai.APIConnectionError as e:
            print(messages)
            print(type(e), e)
            time.sleep(API_RETRY_SLEEP)
        except openai.InternalServerError as e:
            print(messages)
            print(type(e), e)
            time.sleep(API_RETRY_SLEEP)
        except Exception as e:
            print(type(e), e)
            break

    return output


class HuggingFaceClassifier:
    def __init__(self, model_path, device=None):
        print("Loading model and tokenizer...")
        self.device = device or torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.pipeline = pipeline(
            "text-classification",
            model=model_path,
            tokenizer=model_path,
            device=self.device,
        )

    def classify_batch(self, input_texts, batch_size=8):
        results = self.pipeline(input_texts, batch_size=batch_size, truncation=True)
        return [res["label"] == "LABEL_1" for res in results]