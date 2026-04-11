import os
import spacy
import nltk
import numpy as np
import base64
import matplotlib.pyplot as plt
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv, find_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from huggingface_hub import login
from huggingface_hub import InferenceClient
from ultralytics import YOLO
from constants.color_tone_constants import get_color_tone, get_font_color

nltk.download("vader_lexicon")
nlp = spacy.load("en_core_web_sm")


def keyword_extractor(description: str) -> list[str]:
    keywords = []
    doc = nlp(description)
    for token in doc.noun_chunks:
        keywords.append(token.text)

    return keywords


def load_tokens():
    load_dotenv(find_dotenv(), override=True)
    api_gemini_token = os.getenv("GEMINI_API_KEY")
    api_key_hf = os.getenv("HF_TOKEN")
    return api_gemini_token, api_key_hf


def get_poster_color_tone(description: str, genre: str) -> tuple[str, str]:

    if genre is not None and genre != "":
        return get_color_tone(genre), get_font_color(genre)

    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(description)
    sentiment = max(scores, key=scores.get)
    return get_color_tone(sentiment), get_font_color(sentiment)


def calculate_reward(extracted_img_objects, visual_concepts):
    similarity_score = []
    for v_concept in visual_concepts:
        v_obj = nlp(v_concept)
        score = -np.inf
        for extracted_obj in extracted_img_objects:
            extracted_obj = nlp(extracted_obj)
            sim = v_obj.similarity(extracted_obj)
            if sim > score:
                score = sim

        similarity_score.append(score)

    return np.mean((similarity_score))


class PosterGenerator:
    def __init__(self, title: str, description: str, genre: str, episodes: int = 2):
        self.title = title
        self.description = description
        self.genre = genre
        self.episodes = episodes

        self.api_gemini_token, self.api_key_hf = self._load_tokens()
        self.color_tone, self.font_color = get_poster_color_tone(description, genre)
        self.visual_concepts = keyword_extractor(description)
        self.chat_history = []
        self.base_reward = -np.inf
        self.iteration = 0

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite-preview",
            temperature=0,
            api_key=self.api_gemini_token,
        )
        self.client = InferenceClient(
            provider="hf-inference",
            api_key=self.api_key_hf,
        )

    @staticmethod
    def _load_tokens() -> tuple[str, str]:
        load_dotenv(find_dotenv(), override=True)
        api_gemini_token = os.getenv("GEMINI_API_KEY")
        api_key_hf = os.getenv("HF_TOKEN")
        return api_gemini_token, api_key_hf

    def _build_prompt(self) -> str:
        style_suffix = (
            "minimal flat design poster, simple clean composition, "
            "no realistic textures, no photography, "
            "2D illustration"
        )
        base_prompt = (
            f"Generate a single Stable Diffusion prompt for a minimal poster using top 3 visual concepts "
            f"from this {', '.join(self.visual_concepts)} with the poster title as {self.title} nothing else on the title, "
            f"poster color tone as {self.color_tone} and title font color as `{self.font_color}`. "
            f"Style must be: {style_suffix}. "
            f"Return only the prompt text sentence, nothing else."
        )
        if self.iteration == 0 and self.base_reward == -np.inf:
            prompt = base_prompt

        else:
            prompt = (
                f"You are optimising the Stable Diffusion prompt for a minimal poster. "
                f"Your current reward is {self.base_reward:.4f} and you need to improve it. "
                f"The reward is calculated by extracting objects in the poster and averaging "
                f"the similarity score between {', '.join(self.visual_concepts)} and extracted objects. "
                f"The poster MUST remain minimal and flat — no realism, no photography. "
                f"Modify this prompt to improve the reward: "
                + base_prompt
            )

        return prompt

    def sd_prompt_generator(self) -> str:
        prompt = self._build_prompt()
        self.chat_history.append(HumanMessage(content=prompt))
        response = self.llm.invoke(self.chat_history)
        return (
            response.content[0]["text"]
            if isinstance(response.content, list)
            else response.content
        )

    def sd_image_generator(self, prompt: str, filename: str):
        negative_prompt = (
            "realistic, photography, 3d render, photorealistic, detailed textures, "
            "gradients, shadows, complex background, cluttered, noisy, cinematic, "
            "portrait, landscape photography, hyper detailed"
        )
        image = self.client.text_to_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=600,
            width=400,
            model="black-forest-labs/FLUX.1-schnell",
        )
        os.makedirs("./output", exist_ok=True)
        image.save(f"./output/{filename}")

    def image_extractor(self, filename: str):
        extractor_llm = extractor_llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite-preview",
            temperature=0,
            api_key=self.api_gemini_token,
        )

        with open(filename, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
            response = extractor_llm.invoke(
                [
                    HumanMessage(
                        content=[
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                },
                            },
                            {
                                "type": "text",
                                "text": "Extract top 3 visual concepts from this image as a comma separated list. Return only the list, nothing else.",
                            },
                        ]
                    )
                ]
            )
        return (
            response.content[0]["text"]
            if isinstance(response.content, list)
            else response.content
        )

    def generate(self) -> str:
        img_dict = {}
        for _ in range(self.episodes):
            img_prompt = self.sd_prompt_generator()
            print(f"Iterattion: {self.iteration} Prompt: {img_prompt}")
            filename = f"{self.title}_{self.iteration}.png"
            self.sd_image_generator(img_prompt, filename)
            filepath = f"./output/{filename}"
            extracted_objects = (self.image_extractor(filepath)).split(",")
            similarity_score = calculate_reward(extracted_objects, self.visual_concepts)
            print(f"Iteration: {self.iteration} Reward: {similarity_score}")
            img_dict[filename] = similarity_score
            self.base_reward = similarity_score
            self.iteration += 1

        best_img = max(img_dict, key=img_dict.get)
        other_img = [img for img in img_dict.keys() if img != best_img]
        print(f"Best image: {best_img} with reward {img_dict[best_img]:.4f}")
        return best_img,other_img


if __name__ == "__main__":
    title = input("Enter the title of the poster: ")
    description = input("Enter the description of the poster: ")
    genre = input("Enter Genre: ")

    generator = PosterGenerator(title, description, genre)
    best_img,other_img = generator.generate()
