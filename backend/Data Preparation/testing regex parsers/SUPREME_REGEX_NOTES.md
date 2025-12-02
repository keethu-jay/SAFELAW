# Supreme Court Regex Parser – Quick Test Notes

This folder is for **one-off testing** of the UK Supreme Court (seriatim) regex parser defined in `cenral_parser.py` and `court_config.yaml`.

Goal: run the parser on a few real XML judgments and see if regex expressions can be succesfully used and applied.

---

## Folder Layout

- `supreme_samples/`  
  Raw judgment .xml files for testing (downloaded from the national archives website).

- `output_json/`  
  JSON produced by `supreme_parser_test.py` for each sample, containing:
  - `citation`
  - `court_level`
  - `chunks[]` with:
    - `para_number`
    - `content_text`
    - `author_name`
    - `opinion_type`
    - `section_type`
    - `has_citation`
    - `cited_cases`

- `supreme_parser_test.py`  
  CLI script that runs `process_document` on all files in `supreme_samples/` and writes JSON into `output_json/`. It is not connected to the yaml for modularity and it is not connected to the central parser.

---


## Results

I ran `supreme_parser_text.py` and the json outputs were not very accurate and the main issue was correctly identifying the content of the paragraphs. This also looks like a nightmare to maintain and update as it seems the structure of supreme court judments change frequently and is not standardized.
