import sys
from openai import OpenAI

def main():
    client = OpenAI(api_key='')

    if len(sys.argv) < 2:
        print("Usage: python3 main.py <path to text file1> <path to text file2> <path to text file3> ...")
        return -1

    # save texts from files in list text_list
    text_list = []
    for i in range(1, len(sys.argv)):
        file = open(sys.argv[i], "r")
        text_list.append(file.read())
        file.close()

    message_string = "Überprüfe die folgenden Texte auf inhaltliche ähnlichkeit. Antworte mit einer Zahl zwischen 0 und 1. Nenne die Texte die sich am meisten ähneln und deren Dateinamen, welche in klammern vor dem = vermerkt sind:\n"
    counter = 1
    for text in text_list:
        message_string += "Text" + str(counter) + "(" + sys.argv[counter] + ")" + " = " + text
        counter+=1

    print(message_string)

    # https://platform.openai.com/docs/guides/rate-limits/usage-tiers?context=tier-free
    # using OpenAI API
    completion = client.chat.completions.create(
      model="gpt-4",
      messages=[
      {"role": "user", "content": message_string}]
    )

    # using LocalAi
    # completion = client.chat.completions.create(
    #     model="luna-ai-llama2-uncensored.Q6_K.gguf",
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": "How do I output all files in a directory using Python?",
    #         },
    #     ],
    # )

    print(completion.choices[0].message.content)
    

if __name__ == "__main__":
    main()
