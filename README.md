
## Prerequisites

- Python 3.x
- `openai` library (install using `pip install openai`)
- `whoosh` library (install using `pip install whoosh`)
- `nltk` library (install using `pip install nltk`)

## Setup

1. **Obtain OpenAI API Key:**
   Obtain an OpenAI API key from [OpenAI](https://beta.openai.com/signup/). Replace the placeholder API key in the code with your actual key:

   ```python
   openai.api_key = "your_api_key_here"
   ```

2. **Set Dataset Path:**
   Update the `documents_path` variable with the path to your dataset. The provided default is a placeholder:

   ```python
   documents_path = "C:\path\to\your\dataset"
   ```

3. **Create Index:**
   Run the script and choose option 1 to create the index.

## Usage

- **Option 2: Compare Search Results:**
  Compare the search results using two different methods (with and without GPT-3.5 Turbo) on a set of predefined questions.

- **Option 3: Put a Question:**
  Enter a category and a question to retrieve an answer from the indexed content. The script will provide both standard search results and results enhanced with GPT-3.5 Turbo.

- **Option 4: Exit:**
  Exit the program.

## Notes

- The indexing process involves parsing Wikipedia documents, tokenizing, stemming, and removing stop words.

- The question-answering process includes a combination of standard search and GPT-3.5 Turbo-generated prompts for enhanced results.

- The script includes error handling for rate limit issues with the OpenAI API.

- The `compare_search_results` function evaluates and compares the performance of the search methods.

## Acknowledgments

- This script uses the OpenAI GPT-3.5 Turbo model for natural language processing.

- The Whoosh library is used for creating the search index.

- NLTK is utilized for text processing tasks.

**Note:** Ensure compliance with OpenAI's usage policies when utilizing the GPT-3.5 Turbo model.
