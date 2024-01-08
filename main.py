import sys
import os
from openai import OpenAI
from dotenv import load_dotenv
import pypdf
import csv
import itertools
from dataclasses import dataclass
import threading
import time

# red text color and clear text color
red = '\033[91m'
clear_color = '\033[0m'

# clear terminal
cls = lambda: os.system('cls' if os.name=='nt' else 'clear')
done = False

# class to store information of Text
@dataclass
class text_class:
    data: str
    filename: str
    csv_row: int

# takes path to file as input and extracts text from PDF file
def extract_pdf_text(pdf_file) -> text_class:
    pdf_text = text_class("", pdf_file, -1)
    try:
        reader = pypdf.PdfReader(pdf_file)
    except Exception:
        print(f"{red}couldn't open file {clear_color} {pdf_file}")
    else:
        for j in range(0, len(reader.pages)): 
            pdf_text.data += reader.pages[j].extract_text()
        pdf_text.data += "\n"
    finally:
        return pdf_text
# -------------------------------------------------------------------------

# takes path to file as input and extract text from txt file
def extract_txt_text(txt_file) -> text_class:
    return_string = text_class("", txt_file, -1)
    file = None

    try:
        file = open(txt_file, "r")
    except IOError:
        print(f"{red}couldn't open file {clear_color} {txt_file}")
    else:
        return_string.data = file.read()
    finally:
        if file: file.close()
        return return_string
# -------------------------------------------------------------------------

# ---------------extract CSV data------------------------------------------
def extract_csv_file(csv_file):
    with open(csv_file, newline='') as csvfile:
        csv_reader = csv.reader(csvfile)
        
        return list(csv_reader)
# --------------------------------------------------------------------------

# ----------------Loading Bar-----------------------------------------------
def loading_spinner():
    spinner = itertools.cycle(['-', '/', '|', '\\'])
    sys.stdout.write("Loading ")
    while done == False:
        sys.stdout.write(next(spinner))   # write the next character
        sys.stdout.flush()                # flush stdout buffer (actual character display)
        time.sleep(0.1)
        sys.stdout.write('\b')            # erase the last written char
# --------------------------------------------------------------------------

# ----------------chatgpt response------------------------------------------
def chatgpt_response(client, message_string):
    # https://platform.openai.com/docs/guides/rate-limits/usage-tiers
    # using OpenAI API
    response = client.chat.completions.create(
       model="gpt-4",
       messages=[
       {"role": "system", "content": "Du bist ein Experte der deutschen Literatur und analysierst beruflich Texte auf ihren Inhalt"},
      # {"role": "user", "content": predefined_prompt},
      # {"role": "assistant", "content": response_log},
       {"role": "user", "content": message_string}
        ],
       seed=1337,
       temperature=0.2
     )

    return response
    
    # print("\n")
    # print(response.choices[0].message.content)
# --------------------------------------------------------------------------

def main():
    client = OpenAI(api_key=os.getenv('OPENAI-API-KEY'))

    if len(sys.argv) < 2:
        print("Usage: python3 main.py <path to text file1> <path to text file2> <path to text file3> ...")
        return -1

    # save texts from files in list text_list
    text_list = []
    for i in range(1, len(sys.argv)):
        if os.path.splitext(sys.argv[i])[1] == ".txt":
            text_list.append(extract_txt_text(sys.argv[i]))

        elif os.path.splitext(sys.argv[i])[1] == ".pdf":
            text_list.append(extract_pdf_text(sys.argv[i]))

        elif os.path.splitext(sys.argv[i])[1] == ".csv":
             # csv_rows = extract_csv_file(sys.argv[i])

             # counter = 1
             # for row in csv_rows:
             #     text_list.append(text_class(''.join(row), sys.argv[i], counter))
             #     counter+=1

             with open(sys.argv[i], newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                row_count = 2
                for row in reader:
                    #print(row['Name:'], row['Text:'])
                    text_list.append(text_class(row['Text:'], sys.argv[i], row_count))
                    row_count += 1

        else:
            print(f"{red}invalid file extension {clear_color} input either .txt or .pdf files")

    message_string = ""
    predefined_prompt = "Überprüfe die folgenden Texte eizelnd miteinander auf inhaltliche ähnlichkeit auch wenn sie aus der gleichen Datei sind. Liste die Texte unter 'Ähnlichkeitswert:\\n' zuerst mit einer Zahl zwischen 0 und 1, wobei 0 für 'ähneln sich nicht' und 1 für 'ähneln sich vollkommen' stehen und nenne mit einem '-' getrennt dahinter die Texte, die die selbe Ähnlichkeit haben und nenne deren Dateinamen, welche in Klammern hinter dem '=' vermerkt sind sowie deren Reihe mit 'Reihe: ', falls Reihe:-1 ist nenne die Reihe nicht. Dann erläutere in einem neuen Abschnitt unter 'Analyse:' worin sich die Texte ähneln\n"
    # predefined_prompt = "Überprüfe die folgenden Texte eizelnd miteinander auf inhaltliche ähnlichkeit. Antworte zuerst mit einer Zahl zwischen 0 und 1, wobei 0 für 'ähneln sich nicht' und 1 für 'ähneln sich vollkommen' stehen und nenne dahinter die Texte, die die selbe Ähnlichkeit haben und deren Dateinamen, welche in Klammern hinter dem '=' vermerkt sind. Dann erläutere in einem neuen Abschnitt worin sich die Texte ähneln\n"
    # predefined_prompt = "Überprüfe die folgenden Texte auf inhaltliche ähnlichkeit. Antworte zuerst mit einer Zahl zwischen 0 und 1 und nenne dahinter die Texte. Nenne dann die Texte die sich am meisten ähneln und deren Dateinamen, welche in klammern vor dem = vermerkt sind:\n"
    while message_string == "":
        input_num = input(f"\nenter 1, 2 or 9 in terminal\n1: {predefined_prompt}2: use own input prompt\n9: exit the program\n\n")

        match input_num:
            case "1":
                message_string = predefined_prompt
            case "2":
                message_string = input("enter input prompt to use: ")
            case "9":
                exit()
            case _:
                message_string = ""
                cls()

    counter = 1 
    for text in text_list:
        message_string += f"Text {str(counter)} ({text.filename}) Reihe:{text.csv_row} = {text.data}\n"
        counter+=1

    response_log = extract_txt_text("response_log.txt")

    # start loading bar in different thread
    t = threading.Thread(target=loading_spinner)
    t.start()

    response = chatgpt_response(client, message_string)

    # set global varaible done to True to stop loading bar
    global done
    done = True
    cls()

    print(response.choices[0].message.content)



if __name__ == "__main__":
    load_dotenv()
    main()
