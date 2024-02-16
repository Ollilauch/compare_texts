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
import json

# red text color and clear text color
red = '\033[91m'
clear_color = '\033[0m'

# clear terminal
cls = lambda: os.system('cls' if os.name=='nt' else 'clear')
done = False

# class to store information of Text
@dataclass
class text_class:
    text_ID: int
    data: str
    filename: str
    csv_row: int
    similarity_scores: dict
    similarity_keyword: str
    text_number: int


# takes path to file as input and extracts text from PDF file
def extract_pdf_text(pdf_file, text_number) -> text_class:
    pdf_text = text_class(-1, "", pdf_file, -1, dict(), "", text_number)
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
def extract_txt_text(txt_file, text_number) -> text_class:
    return_string = text_class(-1, "", txt_file, -1, dict(), "", text_number)
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

def create_row(text_IDs, input_text_ID: str) -> dict:
    row = {}
    row['Reihe'] = str(input_text_ID)

    for text in text_IDs:
        #if text_IDs[text].similarity_scores[str(input_text_ID)] != None and text_IDs[text].similarity_scores[str(input_text_ID)] > 0.6:
        #   row[str(text_IDs[text].text_ID)] = "! "+ str(text_IDs[text].similarity_scores[str(input_text_ID)]) + " !"
        #elif text_IDs[text].similarity_scores[str(input_text_ID)] != None and text_IDs[text].similarity_scores[str(input_text_ID)] <= 0.6:
        row[str(text_IDs[text].text_ID)] = str(text_IDs[text].similarity_scores[str(input_text_ID)])
    return row


def create_csv_matrix(text_IDs):
    with open('output.csv', 'w', newline='') as csvfile:
        header = ['Reihe']
        for row in text_IDs:
            # DEBUG
            print(str(text_IDs[row].text_ID))
            header.append(str(text_IDs[row].text_ID))
        
        output_writer = csv.DictWriter(csvfile, delimiter=',', fieldnames = header)
        output_writer.writeheader()
        for text in text_IDs:
            output_writer.writerow(create_row(text_IDs, str(text_IDs[text].text_ID)))

def extend_list(text_IDs):
    for text in text_IDs:
        for text2 in text_IDs:
            text_IDs[text].similarity_scores[text2] = None

def add_similarityScores(index1: str, index2: str, score: float, text_IDs):
    text_IDs[index1].similarity_scores[index2] = score
    text_IDs[index2].similarity_scores[index1] = score

        
def add_similarity_from_json(text_IDs, input_json: str):
    try:
        json_data = json.loads(input_json)
    except json.decoder.JSONDecodeError:
        print("invalid JSON")
        replaced  = input_json.replace("```json", "", 1)
        replaced  = replaced.replace("```", "", 1)
        json_data = json.loads(replaced)

    extend_list(text_IDs)
    
    text1_index = None
    text2_index = None
    score       = None

    for data in json_data["similarityScores"]:
        if 'ID' not in data['pair']:
            text1_index = data['pair'][0]
            text2_index = data['pair'][1]
        elif 'text1' in data['pair']:
            text1_index = data['pair']['ID']['text1']
            text2_index = data['pair']['ID']['text2']
        else:
            text1_index = data['pair']['ID'][0]
            text2_index = data['pair']['ID'][1]

        score        = data['score']
        #score       = data['pair']['score']
        add_similarityScores(str(text1_index), str(text2_index), float(score), text_IDs)
        

def contains(list, filter):
    for x in list:
        if filter(x):
            return x
    return None

def sort_similarity(text):
    return text.similarity

#def create_output_from_json(text_list):
#    output = "Ähnlichkeitswerte:"

#    line = ""

#   for text in text_list:
        
    
#    cls()
#    print(output)

# ----------------chatgpt response------------------------------------------
def chatgpt_response(client, message_string):
    # https://platform.openai.com/docs/guides/rate-limits/usage-tiers
    # using OpenAI API
    response = client.chat.completions.create(
       model="gpt-4-turbo-preview",
       messages=[
       #{{"role": "system", "content": "Du bist ein Experte der deutschen Literatur und analysierst beruflich Texte auf ihren Inhalt"},
        {"role": "system", "content": "You're a german professor that specializes in comparing texts on their semantic similarities and give your scores as a JSON"},
       {"role": "user", "content": message_string}
        ],
       seed=1337,
       temperature=0.0
     )

    return response
    
# --------------------------------------------------------------------------

def main():
    client = OpenAI(api_key=os.getenv('OPENAI-API-KEY'))

    text_IDs = {}

    if len(sys.argv) < 2:
        print("Usage: python3 main.py <path to text file1> <path to text file2> <path to text file3> ...")
        return -1

    # save texts from files in list text_list
    text_list = []
    tmp_text_numer = 0
    for i in range(1, len(sys.argv)):
        if os.path.splitext(sys.argv[i])[1] == ".txt":
            text_list.append(extract_txt_text(sys.argv[i], tmp_text_numer))
            tmp_text_numer+=1

        elif os.path.splitext(sys.argv[i])[1] == ".pdf":
            text_list.append(extract_pdf_text(sys.argv[i], tmp_text_numer))
            tmp_text_numer+=1

        elif os.path.splitext(sys.argv[i])[1] == ".csv":
             with open(sys.argv[i], newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                row_count = 2

                for row in reader:
                    #print(row['Name:'], row['Text:'])
                    if not row['ID']:
                        row_count = int(reader.line_num)
                    else:
                        if row_count < 100:
                            print(row['Beschreibung'])
                            text_IDs[row['ID']] = (text_class(int(row['ID']), row['Beschreibung'], sys.argv[i], int(reader.line_num), dict(), "", tmp_text_numer))
                            row_count += 1
                            tmp_text_numer+=1
                        else:
                            break

        else:
            print(f"{red}invalid file extension {clear_color} input either .txt or .pdf files")

    message_string = ""
    predefined_prompt = "compare the following texts on their semantic similarity. return only a JSON not named 'json' with an Array named 'similarityScores' the Array holds a 'pair' Object which constists of only the Textnumber in 'ID:' being compared and the value 'score' representing their similarity with a decimal between 0 and 1. Fill the JSON with all the Texts you have been given.\n"
    #predefined_prompt = "Überprüfe die folgenden Texte einzeln miteinander auf inhaltliche Ähnlichkeit, auch wenn sie aus der gleichen Datei sind. Gebe ein Json zurück mit dem Objekt 'Ähnlichkeitswerte:'. Unter dem Objekt 'Ähnlichkeitswerte:' soll für jede Textnummer ein Objekt sein. Fülle jedes Textnummer Objekt mit dem Wert 'similarities' in dem alle Ähnlichkeitswerte stehen. Berechne den Ähnlichkeitswert indem du den Text mit der nummer des auzufüllenden Textnummer Objekts mit allen anderen Texten vergleichst und eine Nummer zwischen 0 und 1 zurück gibst.\n"     
    #predefined_prompt = "Überprüfe die folgenden Texte einzeln miteinander auf inhaltliche Ähnlichkeit, auch wenn sie aus der gleichen Datei sind. Gebe ein Json zurück in dem alle Texte mit den Werten 'filename', 'csv_row', 'similarity', 'texts_similar' und 'similarity_keyword' im Objekt 'Texte' ist. Fülle, den Wert 'filename' mit dem Wert in der Klammer, den Wert 'csv_row' mit dem Wert hinter 'Reihe:', den Wert 'similarity' mit einer dezimal Zahl zwischen 0 und 1, wobei 0 für 'ähneln sich nicht' und 1 für 'ähneln sich vollkommen' stehen, den Wert 'texts_similar' mit den Text nummern mit dem sich der Text ähnelt und den Wert 'similarity_keyword' mit einem Stichwort, welches am besten beschreibt, worin sich die Texte ähneln benutze dasselbe Stichwort f+r Texte dich sich ähneln\n"
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

    for text in text_IDs:
        message_string += f"Text ID:{str(text_IDs[text].text_ID)} ({text_IDs[text].filename}) Reihe:{str(text_IDs[text].csv_row)} = {text_IDs[text].data}\n"

    # DEBUG
    print(message_string)
    # start loading bar in different thread
    t = threading.Thread(target=loading_spinner)
    t.start()

    response = chatgpt_response(client, message_string)

    # set global varaible done to True to stop loading bar
    global done
    done = True
    cls()

    print(response)

    if input_num == '1':
        add_similarity_from_json(text_IDs, response.choices[0].message.content)
        #create_output_from_json(text_list)
        create_csv_matrix(text_IDs)

    elif input_num == '2':
        print(response.choices[0].message.content)
    



if __name__ == "__main__":
    load_dotenv()
    main()
