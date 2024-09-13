from groq import Groq


class GroqClient:
    @staticmethod
    async def get_chat_completion(api_key):
        """Статический метод для создания чат-сообщения и возврата его ответа"""
        client = Groq(api_key=api_key)

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Write a random post for Twitter.",
                }
            ],
            model="llama3-8b-8192",
        )

        content = chat_completion.choices[0].message.content
        clean_content = content.strip('"')

        return clean_content
