import sys
import os
from openai import OpenAI
from dotenv import load_dotenv
import pypdf

red = '\033[91m'
clear_color = '\033[0m'

def main():
    client = OpenAI(api_key=os.getenv('OPENAI-API-KEY'))

    if len(sys.argv) < 2:
        print("Usage: python3 main.py <path to text file1> <path to text file2> <path to text file3> ...")
        return -1

    # save texts from files in list text_list
    file = None
    text_list = []
    for i in range(1, len(sys.argv)):
        if os.path.splitext(sys.argv[i])[1] == ".txt":
            try:
                file = open(sys.argv[i], "r")
            except IOError:
                print(f"{red}couldn't open file {clear_color} {sys.argv[i]}")
            
            else:
                text_list.append(file.read())
            finally:
                if file: file.close()

        elif os.path.splitext(sys.argv[i])[1] == ".pdf":
            pdf_text = ""
            try:
                reader = pypdf.PdfReader(sys.argv[i])
            except Exception:
                print(f"{red}couldn't open file {clear_color} {sys.argv[i]}")
            else:
                for j in range(0, len(reader.pages)): 
                    pdf_text += reader.pages[j].extract_text()
                pdf_text += "\n"
                text_list.append(pdf_text)

        else:
            print(f"{red}invalid file extension {clear_color} input either .txt or .pdf files")
        

    input_num = input("\ntype 1, 2 or 9 in terminal\n1: use predifinied input prompt - Überprüfe die folgenden Texte auf inhaltliche ähnlichkeit. Antworte mit einer Zahl zwischen 0 und 1. Nenne die Texte die sich am meisten ähneln und deren Dateinamen, welche in klammern vor dem = vermerkt sind:\n2: use own input prompt\n9: exit the program\n")

    message_string = ""
    match input_num:
        case "1":
            message_string = "Überprüfe die folgenden Texte auf inhaltliche ähnlichkeit. Antworte mit einer Zahl zwischen 0 und 1. Nenne die Texte die sich am meisten ähneln und deren Dateinamen, welche in klammern vor dem = vermerkt sind:\n"
        case "2":
            message_string = input("enter input prompt to use: ")
        case "9":
            exit()

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
       {"role": "system", "content": "Du bist ein Experte der deutsche Literatur und analysierst Beruflich Texte auf ihren Inhalt"},
       {"role": "user", "content": message_string}]
     )

    print(completion.choices[0].message.content)
    

if __name__ == "__main__":
    load_dotenv()
    main()
