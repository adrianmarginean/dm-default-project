import os
import re
import time
import openai
from whoosh import index
from whoosh.fields import TEXT, Schema
import nltk
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from whoosh.qparser import QueryParser
from whoosh.query import Or


schema = Schema(
    title=TEXT(stored=True),
    content=TEXT(stored=True),
)

openai.api_key  = "" ## Insert the API Key

index_path = "wikipedia_index"
documents_path = "C:\code\Master\DM\dm-default-project\dataset" ## Insert your path for the dataset

if not os.path.exists(index_path):
    os.makedirs(index_path)
    

def chat_with_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        return response['choices'][0]['message']['content']

    except openai.error.RateLimitError:
        print(f"Rate limit exceeded. Waiting for reset.")
        time.sleep(100) 
        return chat_with_gpt(prompt)

## Process the file documents and extract the content and the title
## Process contents by tokenizing, stemming, and removing stop words
def extract_title_and_content(file_path):
    ps = PorterStemmer()
    stop_words = set(stopwords.words("english"))

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    non_matches = re.split(r'\n*\[\[(.*?)\]\]\n', content)
    non_matches.pop(0)  

    titles = non_matches[::2]
    contents = non_matches[1::2]

    processed_contents = []
    for cont in contents:
        tokens = nltk.word_tokenize(cont)
        stemmed_tokens = [ps.stem(word) for word in tokens if word.lower() not in stop_words and word.isalnum()]
        processed_contents.append(stemmed_tokens)

    return titles, processed_contents

def create_index():
    ix = index.create_in(index_path, schema)
    with ix.writer() as writer:
        for file_name in os.listdir(documents_path):
            file_path = os.path.join(documents_path, file_name)
            title, content = extract_title_and_content(file_path)
            print(file_name)
            if title and content:
                for i in range(len(content)):
                    cnt = ' '.join(content[i])
                    writer.add_document(title=title[i], content=cnt)
    ix.close()

## Read the contet of the question file and split the information into categories, clues, answers
def read_and_process_questions(file_path="questions.txt"):
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    categories = lines[::4]
    clues = lines[1::4]
    answers = lines[2::4]

    categories = [category.strip() for category in categories]
    clues = [clue.strip() for clue in clues]
    answers = [answer.strip() for answer in answers]

    return categories, clues, answers

def preprocess_text(text):
    ps = PorterStemmer()
    stop_words = set(stopwords.words("english"))
    tokens = nltk.word_tokenize(text)
    return [ps.stem(word) for word in tokens if word.lower() not in stop_words and word.isalnum()]

def build_query_for_text(query_parser, text):
    preprocessed_tokens = preprocess_text(text)
    return [query_parser.parse(word) for word in preprocessed_tokens]

def search_single_query(searcher, combined_query, expected_title):
    results = searcher.search(combined_query)

    if len(results) > 0 and results[0]["title"] == expected_title:
        return 1
    return 0

def search_single_query_with_GPT(searcher, combined_query, expected_title, question, category):
    results = searcher.search(combined_query)

    if results:
        top_results_titles = [result["title"] for result in results[:10]]
        input_gpt = (
            f"Please select one item from the list {top_results_titles} in the category {category}. "
            f"Use the following clue: \"{question}\". No additional text allowed!"
        )

        result_from_chat_GPT = chat_with_gpt(input_gpt)

        if result_from_chat_GPT == expected_title:
            return 1

    return 0

##  Searches an index for questions, evaluates performance, and returns lists of categories and questions that received incorrect responses.
def search_index_in_question_file(index_path="wikipedia_index", chat_GPT_version=True):
    categories, clues, titles = read_and_process_questions()
    ix = index.open_dir(index_path)
    query_parser = QueryParser("content", ix.schema)
    correct_answers = 0
    total_questions = len(clues)
    list_of_questions_wrong_response = []
    list_of_category_wrong_response = []

    for i in range(len(clues)):
        clue_queries = build_query_for_text(query_parser, clues[i])
        category_queries = build_query_for_text(query_parser, categories[i])
        combined_query = Or(clue_queries + category_queries)

        with ix.searcher() as searcher:
            if chat_GPT_version:
                value = search_single_query_with_GPT(searcher, combined_query, titles[i], clues[i], categories[i])
                correct_answers += value
                if value == 0:
                    list_of_questions_wrong_response.append(clues[i])
                    list_of_category_wrong_response.append(categories[i])
            else:
                value = search_single_query(searcher, combined_query, titles[i])
                correct_answers += value
                if value == 0:
                    list_of_questions_wrong_response.append(clues[i])
                    list_of_category_wrong_response.append(categories[i])

    accuracy = correct_answers / total_questions

    if chat_GPT_version:
        print("Evaluation for Chat GPT Version:")
    else:
        print("Evaluation for Non-GPT Version:")
    print(f"Overall P@1: {accuracy:.2%}")
    print(f"Number of Correct Answers: {correct_answers}")
    print(f"Number of Incorrect Answers: {total_questions - correct_answers}")

    return list_of_category_wrong_response, list_of_questions_wrong_response

## This function answer a question
def answer_question(category, question, index_path="wikipedia_index"):
    ix = index.open_dir(index_path)
    query_parser = QueryParser("content", ix.schema)
    clue_queries = build_query_for_text(query_parser, question)
    category_queries = build_query_for_text(query_parser, category)
    combined_query = Or(clue_queries + category_queries)
    with ix.searcher() as searcher:
     results = searcher.search(combined_query)
     if results:
        result = results[0]["title"]
        print(f"Result: {result}")
         
        top_results_titles = [result["title"] for result in results[:10]]
        input_gpt = (
            f"Please select one item from the list {top_results_titles} in the category {category}. "
            f"Use the following clue: \"{question}\". No additional text allowed!"
        )

        result_from_chat_GPT = chat_with_gpt(input_gpt)
        print(f"Result with ChatGPT: {result_from_chat_GPT}")
        
## Used to compare the tho methods 
def compare_search_results(index_path):
    list_category_gpt_version1, list_questions_gpt_version1 = search_index_in_question_file(index_path, False)
    list_category_gpt_version2, list_questions_gpt_version2 = search_index_in_question_file(index_path, True)

    common_categories = set(list_category_gpt_version1) & set(list_category_gpt_version2)
    common_questions = set(list_questions_gpt_version1) & set(list_questions_gpt_version2)

    print("Common Incorrect Categories:")
    print(common_categories)

    print("Common Incorrect Questions:")
    print(common_questions)

def main():
    while True:
        print("Menu:")
        print("1. Create index")
        print("2. Compare Search Results")
        print("3. Put a question")
        print("4. Exit")
        
        choice = input("Enter your choice (1, 2, 3 or 4): ")

        if choice == "2":
            compare_search_results("wikipedia_index")
        elif choice == "1":
            create_index()
        elif choice == "3":
            category = input("Enter category: ")
            question = input("Put question: ")
            answer_question(category, question)
        elif choice == "4":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3 or 4.")

if __name__ == "__main__":
    main()









